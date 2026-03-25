# NeuralVaultCore — Daemon manager (watcher + periodic summarizer + auto-backup)
# Copyright (c) 2025-2026 getobyte — MIT License

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_PID_FILE = "~/.nvc/daemon.pid"
DEFAULT_STATE_FILE = "~/.nvc/daemon.json"

_IS_WINDOWS = sys.platform == "win32"


def _pid_path() -> Path:
    return Path(os.path.expanduser(DEFAULT_PID_FILE))


def _state_path() -> Path:
    return Path(os.path.expanduser(DEFAULT_STATE_FILE))


def _is_running(pid: int) -> bool:
    """Check if a process with given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def status() -> dict:
    """Get daemon status. Returns dict with 'running', 'pid', 'config'."""
    pid_file = _pid_path()
    if not pid_file.exists():
        return {"running": False, "pid": None}

    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        return {"running": False, "pid": None}

    if _is_running(pid):
        state = {}
        state_file = _state_path()
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"running": True, "pid": pid, **state}

    # Stale PID file
    pid_file.unlink(missing_ok=True)
    return {"running": False, "pid": None}


def start(
    watch_paths: Optional[list] = None,
    summarize_interval_hours: float = 1.0,
) -> int:
    """
    Start the NVC daemon.
    Returns PID of the daemon process.
    """
    st = status()
    if st["running"]:
        logger.info("Daemon already running (PID %s)", st["pid"])
        return st["pid"]

    pid_file = _pid_path()
    pid_file.parent.mkdir(parents=True, exist_ok=True)

    # Fork (Unix) or run in foreground (Windows)
    if not _IS_WINDOWS:
        pid = os.fork()
        if pid > 0:
            # Parent
            pid_file.write_text(str(pid))
            state_file = _state_path()
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(
                json.dumps(
                    {
                        "watch_paths": watch_paths or [],
                        "summarize_interval": summarize_interval_hours,
                        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                )
            )
            return pid
        # Child continues below
    else:
        # Windows: write current PID (foreground mode)
        pid_file.write_text(str(os.getpid()))

    # Daemon loop
    _run_daemon(watch_paths or [], summarize_interval_hours)
    return os.getpid()


def stop() -> bool:
    """Stop the running daemon. Returns True if stopped."""
    st = status()
    if not st["running"]:
        logger.info("Daemon is not running.")
        return False

    pid = st["pid"]
    try:
        if _IS_WINDOWS:
            # Windows: SIGTERM not supported, use SIGINT or taskkill
            import subprocess

            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
                check=False,
            )
        else:
            os.kill(pid, signal.SIGTERM)
        # Wait for process to exit
        for _ in range(10):
            if not _is_running(pid):
                break
            time.sleep(0.5)
    except (OSError, ProcessLookupError):
        pass

    _pid_path().unlink(missing_ok=True)
    _state_path().unlink(missing_ok=True)
    return True


def _run_daemon(watch_paths: list, summarize_interval_hours: float) -> None:
    """Main daemon loop — runs watchers and periodic summarizer."""
    from core.config import NVCConfig
    from core.storage import SQLiteStorage

    env_file = Path(__file__).parent.parent / ".env"
    try:
        config = NVCConfig.from_env(env_file if env_file.exists() else None)
        config.validate()
    except Exception as e:
        logger.error("Failed to load daemon config from %s: %s", env_file, e)
        return

    import threading

    stop_event = threading.Event()
    storage = SQLiteStorage(config)

    # Start file watchers in threads
    watcher_threads = []
    if watch_paths:
        try:
            from core.watcher import watch_directory

            for wp in watch_paths:
                ns = f"watch:{Path(wp).name}"
                t = threading.Thread(
                    target=watch_directory,
                    args=(wp, storage, ns),
                    daemon=True,
                )
                t.start()
                watcher_threads.append(t)
                logger.info("Started watcher for %s", wp)
        except ImportError:
            logger.warning("watchdog not installed — file watching disabled")

    # Periodic summarization loop
    interval = summarize_interval_hours * 3600
    last_summary = time.time()
    last_backup = time.time()

    def _handle_signal(signum, frame):
        logger.info("Daemon received signal %d, shutting down.", signum)
        stop_event.set()

    if not _IS_WINDOWS:
        signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info("NVC daemon started (PID %d)", os.getpid())

    try:
        while not stop_event.wait(60):
            now = time.time()
            if now - last_summary >= interval:
                try:
                    from core.summarizer import run_summarize

                    summary = run_summarize(storage, summarize_interval_hours)
                    logger.info("Auto-summary generated: %s", summary[:100])
                except Exception as e:
                    logger.warning("Auto-summary failed: %s", e)
                last_summary = now

            # Auto-backup daily (every 24h)
            if now - last_backup >= 86400:  # 24 hours
                try:
                    from datetime import datetime

                    db_path = Path(config.db_path)
                    if db_path.exists():
                        backup_dir = db_path.parent / "backups"
                        backup_dir.mkdir(exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d")
                        backup_path = backup_dir / f"nvc_auto_{timestamp}.db"
                        if not backup_path.exists():
                            storage.backup_to(backup_path)
                            logger.info("Auto-backup created: %s", backup_path)
                            backups = sorted(backup_dir.glob("nvc_auto_*.db"))
                            for old in backups[:-7]:
                                old.unlink()
                                logger.info("Pruned old backup: %s", old.name)
                except Exception as e:
                    logger.warning("Auto-backup failed: %s", e)
                last_backup = now
    finally:
        storage.close()
        _pid_path().unlink(missing_ok=True)
        _state_path().unlink(missing_ok=True)
