import sqlite3
import pytest
from pathlib import Path
from core.config import NVCConfig
from core.migration import (
    get_schema_version, migrate_to_latest, create_safety_backup,
    CURRENT_SCHEMA_VERSION, _ensure_schema_meta,
)


def test_fresh_db_migrates_to_latest(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    version = migrate_to_latest(conn, db)
    assert version == CURRENT_SCHEMA_VERSION
    conn.close()


def test_schema_meta_created(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    _ensure_schema_meta(conn)
    v = get_schema_version(conn)
    assert v == 0
    conn.close()


def test_composite_pk_after_migration(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    migrate_to_latest(conn, db)
    # Verify composite PK by inserting same key in different namespaces
    conn.execute(
        "INSERT INTO memories (namespace, key, title, content, tags, created_at, updated_at, chars, lines) "
        "VALUES ('ns1', 'k1', 't1', 'c1', '', '2026-01-01', '2026-01-01', 2, 1)"
    )
    conn.execute(
        "INSERT INTO memories (namespace, key, title, content, tags, created_at, updated_at, chars, lines) "
        "VALUES ('ns2', 'k1', 't2', 'c2', '', '2026-01-01', '2026-01-01', 2, 1)"
    )
    conn.commit()
    rows = conn.execute("SELECT * FROM memories WHERE key = 'k1'").fetchall()
    assert len(rows) == 2
    conn.close()


def test_safety_backup_created(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.commit()
    conn.close()
    backup = create_safety_backup(db)
    assert backup.exists()
    assert backup.stat().st_size > 0


def test_safety_backup_nonexistent_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_safety_backup(tmp_path / "nope.db")


def test_fts_works_after_migration(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    migrate_to_latest(conn, db)
    conn.execute(
        "INSERT INTO memories (namespace, key, title, content, tags, created_at, updated_at, chars, lines) "
        "VALUES ('default', 'test', 'Test Title', 'hello world content', 'tag1', '2026-01-01', '2026-01-01', 19, 1)"
    )
    conn.commit()
    results = conn.execute(
        "SELECT m.* FROM memories m JOIN memories_fts f ON m.rowid = f.rowid WHERE memories_fts MATCH '\"hello world\"'"
    ).fetchall()
    assert len(results) >= 1
    conn.close()
