# core/shell_capture.py
"""Shell command capture — called by bash/zsh/powershell hooks."""
from __future__ import annotations

import hashlib
import logging
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Commands to ignore (too trivial to store)
IGNORE_COMMANDS = frozenset({
    "cd", "ls", "ll", "la", "pwd", "clear", "cls", "exit", "quit",
    "history", "whoami", "date", "echo", "cat", "less", "more",
    "top", "htop", "man", "help", "true", "false",
})

MIN_COMMAND_LENGTH = 5
MAX_COMMAND_LENGTH = 1000


def _should_capture(cmd: str) -> bool:
    """Filter out trivial/short commands."""
    cmd_stripped = cmd.strip()
    if len(cmd_stripped) < MIN_COMMAND_LENGTH:
        return False
    first_word = cmd_stripped.split()[0].lower()
    # Strip path prefixes and common wrappers
    first_word = first_word.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return first_word not in IGNORE_COMMANDS


def _dedup_key(cmd: str, hostname: str) -> str:
    """Generate a dedup key from command + hostname."""
    h = hashlib.md5(cmd.encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"shell:{hostname}:{h}"


def capture_command(cmd: str) -> bool:
    """
    Capture a shell command into NVC storage.
    Returns True if stored, False if filtered/skipped.
    Called by shell hooks.
    """
    if not _should_capture(cmd):
        return False

    hostname = platform.node() or "local"
    truncated = cmd[:MAX_COMMAND_LENGTH]
    key = _dedup_key(truncated, hostname)
    namespace = f"shell:{hostname}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    title = f"[{now}] {truncated[:80]}"

    try:
        from core.config import NVCConfig
        from core.storage import SQLiteStorage

        env_file = Path(__file__).parent.parent / ".env"
        config = NVCConfig.from_env(env_file if env_file.exists() else None)
        with SQLiteStorage(config) as storage:
            # Dedup: check if this exact command was already stored recently
            existing = storage.retrieve(key, namespace)
            if existing:
                return False  # Already captured

            storage.store(key, truncated, ["shell", "auto-capture"], title, namespace)
            return True
    except Exception as e:
        # Never crash the user's terminal
        logger.debug("Shell capture failed: %s", e)
        return False


def main():
    """CLI entry point: python -m core.shell_capture 'command here'"""
    if len(sys.argv) < 2:
        return
    cmd = " ".join(sys.argv[1:])
    capture_command(cmd)


if __name__ == "__main__":
    main()
