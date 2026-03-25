# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Migration framework — schema versioning + data migration
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 2  # v2.0: (namespace, key) composite PK
APP_VERSION = "1.0.0"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get current schema version. Returns 0 if no schema_meta table."""
    try:
        row = conn.execute("SELECT schema_version FROM schema_meta LIMIT 1").fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0


def _ensure_schema_meta(conn: sqlite3.Connection) -> None:
    """Create schema_meta table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_meta (
            schema_version INTEGER NOT NULL,
            app_version TEXT NOT NULL,
            last_migrated_at TEXT NOT NULL
        )
    """)
    if conn.execute("SELECT COUNT(*) FROM schema_meta").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO schema_meta (schema_version, app_version, last_migrated_at) VALUES (?, ?, ?)",
            (0, APP_VERSION, _utcnow()),
        )
    conn.commit()


def _update_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(
        "UPDATE schema_meta SET schema_version=?, app_version=?, last_migrated_at=?",
        (version, APP_VERSION, _utcnow()),
    )
    conn.commit()


def create_safety_backup(db_path: Path) -> Path:
    """Create a safety backup before migration. Raises if backup fails."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    backup_path = db_path.parent / f"{db_path.stem}_pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
    try:
        shutil.copy2(str(db_path), str(backup_path))
        logger.info("Safety backup created: %s", backup_path)
        return backup_path
    except OSError as e:
        raise RuntimeError(f"Cannot create safety backup: {e}. Migration refused.") from e


def _migrate_v0_to_v1(conn: sqlite3.Connection) -> None:
    """v0→v1: Create base tables if missing, add embedding/content_hash/short_summary columns."""
    logger.info("Migrating schema v0 → v1...")

    # Create base tables if this is a fresh DB (no memories table yet)
    conn.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS memories (
            key        TEXT PRIMARY KEY,
            namespace  TEXT NOT NULL DEFAULT 'default',
            title      TEXT NOT NULL,
            content    TEXT NOT NULL,
            tags       TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            chars      INTEGER NOT NULL DEFAULT 0,
            lines      INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS memory_versions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            key       TEXT NOT NULL,
            title     TEXT NOT NULL,
            content   TEXT NOT NULL,
            tags      TEXT NOT NULL DEFAULT '',
            namespace TEXT NOT NULL DEFAULT 'default',
            saved_at  TEXT NOT NULL,
            version   INTEGER NOT NULL
        );
    """)

    # Add missing columns
    for col, typedef in [
        ("embedding", "BLOB"),
        ("content_hash", "TEXT"),
        ("short_summary", "TEXT"),
    ]:
        try:
            conn.execute(f"SELECT {col} FROM memories LIMIT 0")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE memories ADD COLUMN {col} {typedef}")
            logger.info("Added column: memories.%s", col)

    conn.commit()


def _migrate_v1_to_v2(conn: sqlite3.Connection) -> None:
    """v1→v2: Change PK from key to (namespace, key). Namespace-aware versions."""
    logger.info("Migrating schema v1 → v2 (composite PK)...")

    # Create new tables with correct schema
    conn.executescript("""
        -- New memories table with composite PK
        CREATE TABLE IF NOT EXISTS memories_new (
            namespace  TEXT NOT NULL DEFAULT 'default',
            key        TEXT NOT NULL,
            title      TEXT NOT NULL,
            content    TEXT NOT NULL,
            tags       TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            chars      INTEGER NOT NULL DEFAULT 0,
            lines      INTEGER NOT NULL DEFAULT 0,
            embedding  BLOB,
            content_hash TEXT,
            short_summary TEXT,
            PRIMARY KEY (namespace, key)
        );

        -- New versions table namespace-aware
        CREATE TABLE IF NOT EXISTS memory_versions_new (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            namespace TEXT NOT NULL DEFAULT 'default',
            key       TEXT NOT NULL,
            title     TEXT NOT NULL,
            content   TEXT NOT NULL,
            tags      TEXT NOT NULL DEFAULT '',
            saved_at  TEXT NOT NULL,
            version   INTEGER NOT NULL
        );
    """)

    # Copy data from old tables
    # Check if old table exists and has data
    try:
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        if count > 0:
            conn.execute("""
                INSERT OR IGNORE INTO memories_new
                    (namespace, key, title, content, tags, created_at, updated_at,
                     chars, lines, embedding, content_hash, short_summary)
                SELECT namespace, key, title, content, tags, created_at, updated_at,
                       chars, lines, embedding,
                       CASE WHEN content_hash IS NOT NULL THEN content_hash ELSE NULL END,
                       CASE WHEN short_summary IS NOT NULL THEN short_summary ELSE NULL END
                FROM memories
            """)
            logger.info("Copied %d memories to new schema.", count)
    except sqlite3.OperationalError as e:
        logger.warning("Could not copy memories: %s", e)

    try:
        ver_count = conn.execute("SELECT COUNT(*) FROM memory_versions").fetchone()[0]
        if ver_count > 0:
            conn.execute("""
                INSERT OR IGNORE INTO memory_versions_new
                    (id, namespace, key, title, content, tags, saved_at, version)
                SELECT id, namespace, key, title, content, tags, saved_at, version
                FROM memory_versions
            """)
            logger.info("Copied %d versions to new schema.", ver_count)
    except sqlite3.OperationalError as e:
        logger.warning("Could not copy versions: %s", e)

    # Atomic swap: drop old, rename new
    conn.executescript("""
        DROP TABLE IF EXISTS memories_fts;
        DROP TABLE IF EXISTS memories;
        DROP TABLE IF EXISTS memory_versions;
        ALTER TABLE memories_new RENAME TO memories;
        ALTER TABLE memory_versions_new RENAME TO memory_versions;
    """)

    # Recreate indexes
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_memories_namespace ON memories(namespace);
        CREATE INDEX IF NOT EXISTS idx_memories_updated ON memories(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_versions_nskey ON memory_versions(namespace, key, version DESC);

        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
            USING fts5(key, title, content, tags,
                       content='memories',
                       content_rowid='rowid');

        -- Rebuild FTS index from new table
        INSERT INTO memories_fts(memories_fts) VALUES('rebuild');

        -- Recreate triggers
        CREATE TRIGGER IF NOT EXISTS memories_ai
            AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, key, title, content, tags)
                VALUES (new.rowid, new.key, new.title, new.content, new.tags);
            END;

        CREATE TRIGGER IF NOT EXISTS memories_ad
            AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, key, title, content, tags)
                VALUES ('delete', old.rowid, old.key, old.title, old.content, old.tags);
            END;

        CREATE TRIGGER IF NOT EXISTS memories_au
            AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, key, title, content, tags)
                VALUES ('delete', old.rowid, old.key, old.title, old.content, old.tags);
                INSERT INTO memories_fts(rowid, key, title, content, tags)
                VALUES (new.rowid, new.key, new.title, new.content, new.tags);
            END;
    """)

    conn.commit()
    logger.info("Schema v2 migration complete: (namespace, key) composite PK active.")


MIGRATIONS = {
    1: _migrate_v0_to_v1,
    2: _migrate_v1_to_v2,
}


def migrate_to_latest(conn: sqlite3.Connection, db_path: Path) -> int:
    """
    Run all pending migrations. Returns final schema version.
    Creates safety backup before any migration.
    """
    _ensure_schema_meta(conn)
    current = get_schema_version(conn)

    if current >= CURRENT_SCHEMA_VERSION:
        return current

    # Safety backup before migration
    if db_path.exists() and str(db_path) != ":memory:":
        create_safety_backup(db_path)

    for target_version in range(current + 1, CURRENT_SCHEMA_VERSION + 1):
        migration_fn = MIGRATIONS.get(target_version)
        if migration_fn is None:
            raise RuntimeError(f"No migration function for version {target_version}")
        migration_fn(conn)
        _update_schema_version(conn, target_version)
        logger.info("Migrated to schema version %d", target_version)

    return CURRENT_SCHEMA_VERSION
