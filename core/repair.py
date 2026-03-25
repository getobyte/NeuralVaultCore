# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Repair — maintenance and optimization
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from core.migration import create_safety_backup

if TYPE_CHECKING:
    from core.storage import SQLiteStorage

logger = logging.getLogger(__name__)


def run_repair(storage: SQLiteStorage) -> list:
    """Run repair operations. Returns list of (status, message) tuples."""
    results = []
    conn = storage._conn
    db_path = Path(storage._db_path)

    # 1. Safety backup
    if db_path.exists() and str(db_path) != ":memory:":
        try:
            backup = create_safety_backup(db_path)
            results.append(("OK", f"Safety backup: {backup}"))
        except Exception as e:
            results.append(("ERROR", f"Backup failed: {e}"))
            return results  # Abort if can't backup

    # 2. Integrity check
    try:
        check = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if check == "ok":
            results.append(("OK", "Integrity check passed"))
        else:
            results.append(("ERROR", f"Integrity check: {check}"))
    except Exception as e:
        results.append(("ERROR", f"Integrity check failed: {e}"))

    # 3. Reindex FTS
    try:
        conn.execute("INSERT INTO memories_fts(memories_fts) VALUES('rebuild')")
        conn.commit()
        results.append(("OK", "FTS index rebuilt"))
    except Exception as e:
        results.append(("WARN", f"FTS rebuild skipped: {e}"))

    # 4. Rebuild embeddings (if model available)
    try:
        from core.storage import (
            _get_semantic_model,
            _encode_embedding,
            _build_embedding_text,
        )

        model = _get_semantic_model()
        if model:
            rows = conn.execute(
                "SELECT namespace, key, title, tags, content FROM memories WHERE embedding IS NULL"
            ).fetchall()
            if rows:
                for row in rows:
                    text = _build_embedding_text(row[2], row[3], row[4])
                    vec = model.encode(text, show_progress_bar=False).tolist()
                    blob = _encode_embedding(vec)
                    conn.execute(
                        "UPDATE memories SET embedding=? WHERE namespace=? AND key=?",
                        (blob, row[0], row[1]),
                    )
                conn.commit()
                results.append(("OK", f"Rebuilt {len(rows)} missing embeddings"))
            else:
                results.append(("OK", "All embeddings present"))
        else:
            results.append(("SKIP", "Semantic model not available"))
    except Exception as e:
        results.append(("WARN", f"Embedding rebuild skipped: {e}"))

    # 5. Regenerate short_summary for null entries
    try:
        rows = conn.execute(
            "SELECT namespace, key, content FROM memories WHERE short_summary IS NULL"
        ).fetchall()
        if rows:
            for row in rows:
                summary = row[2][:200].replace("\n", " ").strip()
                conn.execute(
                    "UPDATE memories SET short_summary=? WHERE namespace=? AND key=?",
                    (summary, row[0], row[1]),
                )
            conn.commit()
            results.append(("OK", f"Regenerated {len(rows)} summaries"))
    except Exception as e:
        results.append(("WARN", f"Summary regen skipped: {e}"))

    # 6. Regenerate content_hash for null entries
    try:
        import hashlib

        rows = conn.execute(
            "SELECT namespace, key, content FROM memories WHERE content_hash IS NULL"
        ).fetchall()
        if rows:
            for row in rows:
                h = hashlib.sha256(row[2].encode("utf-8")).hexdigest()
                conn.execute(
                    "UPDATE memories SET content_hash=? WHERE namespace=? AND key=?",
                    (h, row[0], row[1]),
                )
            conn.commit()
            results.append(("OK", f"Regenerated {len(rows)} content hashes"))
    except Exception as e:
        results.append(("WARN", f"Hash regen skipped: {e}"))

    # 7. Vacuum + analyze
    try:
        conn.execute("VACUUM")
        conn.execute("ANALYZE")
        results.append(("OK", "VACUUM + ANALYZE complete"))
    except Exception as e:
        results.append(("WARN", f"Vacuum/analyze skipped: {e}"))

    return results
