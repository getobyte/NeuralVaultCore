# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# File watcher — monitors directories for changes
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)

# Directories and patterns to ignore
IGNORE_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "egg-info",
}

IGNORE_EXTENSIONS: Set[str] = {
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".obj",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".db",
    ".db-journal",
    ".db-wal",
}

DEBOUNCE_SECONDS = 5.0


class FileChangeHandler:
    """Collects file changes with debounce, then stores summary in NVC."""

    def __init__(self, storage, namespace: str, debounce: float = DEBOUNCE_SECONDS):
        self._storage = storage
        self._namespace = namespace
        self._debounce = debounce
        self._pending: dict = {}  # path -> event_type
        self._last_flush = time.time()

    def _should_ignore(self, path: str) -> bool:
        parts = Path(path).parts
        for part in parts:
            if part in IGNORE_DIRS:
                return True
        ext = Path(path).suffix.lower()
        return ext in IGNORE_EXTENSIONS

    def on_change(self, event_type: str, src_path: str) -> None:
        if self._should_ignore(src_path):
            return
        self._pending[src_path] = event_type
        self._maybe_flush()

    def _maybe_flush(self) -> None:
        now = time.time()
        if now - self._last_flush < self._debounce:
            return
        if not self._pending:
            return
        self._flush()

    def _flush(self) -> None:
        if not self._pending:
            return

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        changes = dict(self._pending)
        self._pending.clear()
        self._last_flush = time.time()

        # Build summary
        by_type: dict = {}
        for path, evt in changes.items():
            by_type.setdefault(evt, []).append(path)

        lines = []
        for evt, paths in sorted(by_type.items()):
            lines.append(f"{evt}: {len(paths)} file(s)")
            for p in paths[:10]:  # Limit listed files
                lines.append(f"  {p}")
            if len(paths) > 10:
                lines.append(f"  ... and {len(paths) - 10} more")

        content = "\n".join(lines)
        key = f"watch:{self._namespace}:{now_str}"
        title = f"[{now_str}] {len(changes)} file change(s)"

        try:
            self._storage.store(
                key, content, ["watch", "auto-capture"], title, self._namespace
            )
            logger.info("Stored %d file changes for %s", len(changes), self._namespace)
        except Exception as e:
            logger.warning("Failed to store file changes: %s", e)

    def force_flush(self) -> None:
        """Force flush any pending changes."""
        self._flush()


def watch_directory(
    watch_path: str,
    storage,
    namespace: str,
    debounce: float = DEBOUNCE_SECONDS,
) -> None:
    """
    Watch a directory for changes using watchdog.
    Blocks until interrupted.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        logger.error("watchdog not installed. Install with: pip install watchdog")
        raise SystemExit(1)

    handler = FileChangeHandler(storage, namespace, debounce)

    class _WatchdogAdapter(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                handler.on_change("created", event.src_path)

        def on_modified(self, event):
            if not event.is_directory:
                handler.on_change("modified", event.src_path)

        def on_deleted(self, event):
            if not event.is_directory:
                handler.on_change("deleted", event.src_path)

        def on_moved(self, event):
            if not event.is_directory:
                handler.on_change("moved", f"{event.src_path} -> {event.dest_path}")

    observer = Observer()
    observer.schedule(_WatchdogAdapter(), watch_path, recursive=True)
    observer.start()
    logger.info(
        "Watching %s (namespace: %s, debounce: %.1fs)", watch_path, namespace, debounce
    )

    try:
        while True:
            time.sleep(1)
            handler._maybe_flush()
    except KeyboardInterrupt:
        handler.force_flush()
        observer.stop()
    observer.join()
