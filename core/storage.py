# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Storage layer — abstract protocol + SQLite implementation
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import hashlib
import gc
import json
import logging
import shutil
import sqlite3
import struct
import threading
import time
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
from typing import List, Optional, Protocol

from core.config import NVCConfig
from core.exceptions import ValidationError
from core.models import Memory, StorageStats, Version

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _remove_if_exists(path: Path, retries: int = 10, delay: float = 0.05) -> None:
    """Best-effort removal for SQLite sidecar files that may linger briefly on Windows."""
    for attempt in range(retries):
        try:
            if not path.exists():
                return
            path.unlink()
            return
        except FileNotFoundError:
            return
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


# ──────────────────────────────────────────────────────────────────────────────
# Abstract interface
# ──────────────────────────────────────────────────────────────────────────────


class StorageBackend(Protocol):
    """Protocol for storage backends. Implement this to swap SQLite for PostgreSQL, etc."""

    def store(self, key: str, content: str, tags: List[str],
              title: str, namespace: str) -> Memory: ...

    def retrieve(self, key: str, namespace: str = "default") -> Optional[Memory]: ...

    def delete(self, key: str, namespace: str = "default") -> bool: ...

    def list_all(self, namespace: Optional[str] = None, limit: int = 50, offset: int = 0,
                 namespace_prefix: Optional[str] = None) -> tuple: ...

    def list_recent(self, limit: int = 10) -> List[Memory]: ...

    def search(self, query: str, namespace: Optional[str] = None) -> List[Memory]: ...

    def get_versions(self, key: str, namespace: str = "default") -> List[Version]: ...

    def restore_version(self, key: str, namespace: str = "default",
                        version: int = 1) -> Optional[Memory]: ...

    def list_namespaces(self) -> List[str]: ...

    def get_stats(self) -> StorageStats: ...

    def export_all(self) -> List[Memory]: ...

    def import_all(self, memories: List[dict]) -> int: ...

    def migrate_from_json(self, json_dir: str) -> int: ...

    def search_similar(self, key: str, namespace: str = "default",
                       limit: int = 10) -> List[Memory]: ...


# ──────────────────────────────────────────────────────────────────────────────
# Semantic search — lazy-loaded sentence-transformers
# ──────────────────────────────────────────────────────────────────────────────

_semantic_model = None
_semantic_available: Optional[bool] = None  # None = not checked yet

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def _get_semantic_model():
    """Lazy load sentence-transformers model on first use. Returns None if unavailable."""
    global _semantic_model, _semantic_available
    if _semantic_available is False:
        return None
    if _semantic_model is not None:
        return _semantic_model
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading semantic model '%s' (first use — may download ~80MB)...", EMBEDDING_MODEL)
        _semantic_model = SentenceTransformer(EMBEDDING_MODEL)
        _semantic_available = True
        logger.info("Semantic model loaded successfully.")
        return _semantic_model
    except ImportError:
        logger.info("sentence-transformers not installed — semantic search disabled, using FTS5.")
        _semantic_available = False
        return None
    except Exception as e:
        logger.warning("Failed to load semantic model: %s — falling back to FTS5.", e)
        _semantic_available = False
        return None


def _encode_embedding(vec: list) -> bytes:
    """Pack float list into compact bytes (little-endian float32)."""
    return struct.pack(f"<{len(vec)}f", *vec)


def _decode_embedding(blob: bytes) -> list:
    """Unpack bytes back to float list."""
    n = len(blob) // 4
    return list(struct.unpack(f"<{n}f", blob))


def _cosine_similarity(a: list, b: list) -> float:
    """Cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _batch_cosine_similarity(query_vec: list, embeddings: list) -> list:
    """
    Fast batch cosine similarity using numpy.
    Falls back to sequential pure-Python if numpy unavailable.
    """
    try:
        import numpy as np
        q = np.array(query_vec, dtype=np.float32)
        mat = np.array(embeddings, dtype=np.float32)
        # Normalize
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        mat_norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-10
        mat_normalized = mat / mat_norms
        # Batch dot product
        scores = mat_normalized @ q_norm
        return scores.tolist()
    except ImportError:
        return [_cosine_similarity(query_vec, emb) for emb in embeddings]


def _build_embedding_text(title: str, tags: str, content: str) -> str:
    """
    Build text for embedding generation.
    For short content (<=2000 chars): use full content.
    For long content: extract key sentences to build a ~500 char summary.
    """
    prefix = f"{title} {tags}".strip()

    if len(content) <= 2000:
        return f"{prefix} {content}" if prefix else content

    # Extract key sentences for long content
    lines = content.splitlines()
    # Take first 3 lines (usually the most important)
    first_lines = " ".join(lines[:3])[:300]
    # Take last 2 lines (often conclusions)
    last_lines = " ".join(lines[-2:])[:200] if len(lines) > 5 else ""

    # Sample from middle
    if len(lines) > 10:
        mid = len(lines) // 2
        mid_lines = " ".join(lines[mid:mid+2])[:150]
    else:
        mid_lines = ""

    summary_parts = [prefix, first_lines, mid_lines, last_lines]
    summary = " ".join(p for p in summary_parts if p)

    # Cap at ~500 chars for embedding
    return summary[:500]


# ──────────────────────────────────────────────────────────────────────────────
# SQLite implementation
# ──────────────────────────────────────────────────────────────────────────────


class SQLiteStorage:
    """SQLite + WAL + FTS5 storage backend with thread-safe writes."""

    def __init__(self, config: NVCConfig) -> None:
        self._config = config
        self._db_path = Path(config.db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    @property
    def db_path(self) -> str:
        return str(self._db_path)

    @property
    def config(self) -> NVCConfig:
        return self._config

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> SQLiteStorage:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def backup_to(self, path: str | Path) -> Path:
        backup_path = Path(path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with sqlite3.connect(str(self._db_path)) as conn:
                conn.execute("VACUUM INTO ?", (str(backup_path),))
        except (sqlite3.OperationalError, AttributeError):
            self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            shutil.copy2(str(self._db_path), str(backup_path))

        return backup_path

    def restore_from(self, path: str | Path) -> Path:
        source_path = Path(path)
        if not source_path.exists():
            raise FileNotFoundError(f"Backup file not found: {source_path}")

        self._conn.close()
        self._conn = None
        gc.collect()
        for suffix in ("-wal", "-shm"):
            _remove_if_exists(Path(f"{self._db_path}{suffix}"))
        shutil.copy2(str(source_path), str(self._db_path))
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        return source_path

    # ── Schema ────────────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        """Initialize schema via migration framework."""
        from core.migration import migrate_to_latest
        migrate_to_latest(self._conn, self._db_path)

    # ── Validation ────────────────────────────────────────────────────────

    def _validate(self, key: str, content: str, title: str = "", tags_str: str = "") -> None:
        cfg = self._config
        if not key or not key.strip():
            raise ValidationError("Key cannot be empty.")
        if len(key) > cfg.max_key_length:
            raise ValidationError(f"Key too long (max {cfg.max_key_length} chars).")
        if len(title) > cfg.max_title_length:
            raise ValidationError(f"Title too long (max {cfg.max_title_length} chars).")
        if len(content) > cfg.max_content_length:
            raise ValidationError(f"Content too long (max {cfg.max_content_length} chars).")
        if len(tags_str) > cfg.max_tags_length:
            raise ValidationError(f"Tags too long (max {cfg.max_tags_length} chars).")

    # ── CRUD ──────────────────────────────────────────────────────────────

    def store(self, key: str, content: str, tags: List[str],
              title: str, namespace: str) -> Memory:
        tags_str = ",".join(t.strip() for t in tags if t.strip())
        title = (title or key).strip()
        namespace = namespace or "default"
        self._validate(key, content, title, tags_str)

        now = _utcnow()
        chars = len(content)
        lines = content.count("\n") + 1
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        short_summary = content[:200].replace("\n", " ").strip()

        # Generate embedding if semantic model is available
        embedding_blob = None
        model = _get_semantic_model()
        if model is not None:
            try:
                text_for_embedding = _build_embedding_text(title, tags_str, content)
                vec = model.encode(text_for_embedding, show_progress_bar=False).tolist()
                embedding_blob = _encode_embedding(vec)
            except Exception as e:
                logger.warning("Embedding generation failed for key=%s: %s", key, e)

        with self._write_lock:
            conn = self._conn

            existing = conn.execute(
                "SELECT rowid, * FROM memories WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()

            if existing:
                # Save current version before overwriting
                ver_num = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) FROM memory_versions WHERE namespace = ? AND key = ?",
                    (namespace, key),
                ).fetchone()[0] + 1

                conn.execute(
                    """INSERT INTO memory_versions
                       (namespace, key, title, content, tags, saved_at, version)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (namespace, key, existing["title"], existing["content"],
                     existing["tags"], now, ver_num),
                )

                # Prune old versions — keep last N
                conn.execute(
                    """DELETE FROM memory_versions
                       WHERE namespace = ? AND key = ? AND id NOT IN (
                           SELECT id FROM memory_versions
                           WHERE namespace = ? AND key = ? ORDER BY version DESC LIMIT ?
                       )""",
                    (namespace, key, namespace, key, self._config.max_versions_kept),
                )

                conn.execute(
                    """UPDATE memories
                       SET title=?, content=?, tags=?, namespace=?,
                           updated_at=?, chars=?, lines=?,
                           content_hash=?, short_summary=?, embedding=?
                       WHERE namespace=? AND key=?""",
                    (title, content, tags_str, namespace, now, chars, lines,
                     content_hash, short_summary, embedding_blob,
                     namespace, key),
                )
                created_at = existing["created_at"]
            else:
                conn.execute(
                    """INSERT INTO memories
                       (key, namespace, title, content, tags,
                        created_at, updated_at, chars, lines,
                        content_hash, short_summary, embedding)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (key, namespace, title, content, tags_str,
                     now, now, chars, lines,
                     content_hash, short_summary, embedding_blob),
                )
                created_at = now

            conn.commit()

        clean_tags = [t for t in tags_str.split(",") if t] if tags_str else []
        return Memory(
            key=key, content=content, namespace=namespace, title=title,
            tags=clean_tags, created_at=created_at, updated_at=now,
            chars=chars, lines=lines,
        )

    def retrieve(self, key: str, namespace: str = "default") -> Optional[Memory]:
        row = self._conn.execute(
            "SELECT * FROM memories WHERE namespace = ? AND key = ?",
            (namespace, key),
        ).fetchone()
        return Memory.from_row(dict(row)) if row else None

    def delete(self, key: str, namespace: str = "default") -> bool:
        with self._write_lock:
            cur = self._conn.execute(
                "DELETE FROM memories WHERE namespace = ? AND key = ?",
                (namespace, key),
            )
            self._conn.execute(
                "DELETE FROM memory_versions WHERE namespace = ? AND key = ?",
                (namespace, key),
            )
            self._conn.commit()
            return cur.rowcount > 0

    def list_all(self, namespace: Optional[str] = None, limit: int = 50, offset: int = 0,
                 namespace_prefix: Optional[str] = None) -> tuple:
        if namespace:
            total = self._conn.execute(
                "SELECT COUNT(*) FROM memories WHERE namespace=?", (namespace,)
            ).fetchone()[0]
            rows = self._conn.execute(
                "SELECT * FROM memories WHERE namespace=? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (namespace, limit, offset),
            ).fetchall()
        elif namespace_prefix:
            like_pattern = namespace_prefix + "%"
            total = self._conn.execute(
                "SELECT COUNT(*) FROM memories WHERE namespace LIKE ?", (like_pattern,)
            ).fetchone()[0]
            rows = self._conn.execute(
                "SELECT * FROM memories WHERE namespace LIKE ? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (like_pattern, limit, offset),
            ).fetchall()
        else:
            total = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            rows = self._conn.execute(
                "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()

        sl = self._config.snippet_length
        result: List[Memory] = []
        for row in rows:
            mem = Memory.from_row(dict(row))
            mem.snippet = mem.get_snippet(sl)
            result.append(mem)
        return result, total

    def list_recent(self, limit: int = 10) -> List[Memory]:
        """Return the N most recently updated memories (SQL LIMIT, not Python slice)."""
        rows = self._conn.execute(
            "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        sl = self._config.snippet_length
        result: List[Memory] = []
        for row in rows:
            mem = Memory.from_row(dict(row))
            mem.snippet = mem.get_snippet(sl)
            result.append(mem)
        return result

    def search(self, query: str, namespace: Optional[str] = None) -> List[Memory]:
        if not query or not query.strip():
            return self.list_all(namespace)[0]

        word_count = len(query.strip().split())

        # Semantic search for 3+ word queries when model is available
        if word_count >= 3:
            semantic_results = self._semantic_search(query, namespace)
            if semantic_results is not None:
                return semantic_results

        # FTS5 search (default for short queries, or fallback)
        return self._fts_search(query, namespace)

    _SEMANTIC_COLS = (
        "key, namespace, title, tags, updated_at, chars, lines, "
        "created_at, content_hash, short_summary, embedding"
    )

    def _semantic_search(self, query: str, namespace: Optional[str] = None) -> Optional[List[Memory]]:
        """Cosine similarity search using embeddings. Returns None if unavailable."""
        model = _get_semantic_model()
        if model is None:
            return None

        try:
            query_vec = model.encode(query, show_progress_bar=False).tolist()
        except Exception as e:
            logger.warning("Semantic encoding failed: %s — falling back to FTS5.", e)
            return None

        limit = self._config.search_result_limit

        # Exclude content column — only need embedding + metadata for scoring
        if namespace:
            rows = self._conn.execute(
                f"SELECT {self._SEMANTIC_COLS} FROM memories WHERE namespace = ? AND embedding IS NOT NULL",
                (namespace,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                f"SELECT {self._SEMANTIC_COLS} FROM memories WHERE embedding IS NOT NULL"
            ).fetchall()

        # Decode all embeddings
        row_dicts = []
        embeddings = []
        for row in rows:
            row_dict = dict(row)
            emb_blob = row_dict.get("embedding")
            if not emb_blob:
                continue
            embeddings.append(_decode_embedding(emb_blob))
            row_dicts.append(row_dict)

        if not embeddings:
            return []

        # Batch cosine similarity (numpy-accelerated if available)
        scores = _batch_cosine_similarity(query_vec, embeddings)
        scored = list(zip(scores, row_dicts))
        scored.sort(key=lambda x: x[0], reverse=True)

        sl = self._config.snippet_length
        result: List[Memory] = []
        for score, row_dict in scored[:limit]:
            if score < 0.2:
                break
            # content excluded from query — use short_summary as lightweight placeholder
            if "content" not in row_dict:
                row_dict["content"] = row_dict.get("short_summary", "")
            mem = Memory.from_row(row_dict)
            mem.snippet = mem.get_snippet(sl)
            result.append(mem)
        return result

    def _fts_search(self, query: str, namespace: Optional[str] = None) -> List[Memory]:
        """Full-text search via FTS5 with LIKE fallback."""
        limit = self._config.search_result_limit
        safe_query = '"' + query.replace('"', '""') + '"'

        try:
            if namespace:
                rows = self._conn.execute(
                    """SELECT m.* FROM memories m
                       JOIN memories_fts f ON m.rowid = f.rowid
                       WHERE memories_fts MATCH ? AND m.namespace = ?
                       ORDER BY rank LIMIT ?""",
                    (safe_query, namespace, limit),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """SELECT m.* FROM memories m
                       JOIN memories_fts f ON m.rowid = f.rowid
                       WHERE memories_fts MATCH ?
                       ORDER BY rank LIMIT ?""",
                    (safe_query, limit),
                ).fetchall()
        except sqlite3.OperationalError:
            like = f"%{query}%"
            if namespace:
                rows = self._conn.execute(
                    """SELECT * FROM memories
                       WHERE (content LIKE ? OR title LIKE ? OR key LIKE ?)
                         AND namespace = ?
                       ORDER BY updated_at DESC LIMIT ?""",
                    (like, like, like, namespace, limit),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """SELECT * FROM memories
                       WHERE content LIKE ? OR title LIKE ? OR key LIKE ?
                       ORDER BY updated_at DESC LIMIT ?""",
                    (like, like, like, limit),
                ).fetchall()

        sl = self._config.snippet_length
        result: List[Memory] = []
        for row in rows:
            mem = Memory.from_row(dict(row))
            mem.snippet = mem.get_snippet(sl)
            result.append(mem)
        return result

    # ── Bulk & Similarity ─────────────────────────────────────────────────

    def bulk_store(self, memories: list) -> int:
        """Batch store multiple memories. Returns count of successfully stored."""
        count = 0
        for mem in memories:
            try:
                self.store(
                    mem["key"],
                    mem["content"],
                    mem.get("tags", []),
                    mem.get("title", mem["key"]),
                    mem.get("namespace", "default"),
                )
                count += 1
            except (ValueError, KeyError) as e:
                logger.warning("Bulk store skipped key=%s: %s", mem.get("key", "?"), e)
        return count

    def search_similar(self, key: str, namespace: str = "default",
                       limit: int = 10) -> List[Memory]:
        """Find memories similar to the given key using cosine similarity."""
        # Only fetch embedding — no need for full content
        row = self._conn.execute(
            "SELECT embedding FROM memories WHERE namespace = ? AND key = ?",
            (namespace, key),
        ).fetchone()
        if not row or not row["embedding"]:
            return []

        source_vec = _decode_embedding(row["embedding"])

        # Compare against all other memories with embeddings (exclude content for efficiency)
        rows = self._conn.execute(
            f"SELECT {self._SEMANTIC_COLS} FROM memories WHERE NOT (namespace = ? AND key = ?) AND embedding IS NOT NULL",
            (namespace, key),
        ).fetchall()

        # Decode all embeddings
        row_dicts = []
        embeddings = []
        for r in rows:
            r_dict = dict(r)
            emb_blob = r_dict.get("embedding")
            if not emb_blob:
                continue
            embeddings.append(_decode_embedding(emb_blob))
            row_dicts.append(r_dict)

        if not embeddings:
            return []

        # Batch cosine similarity (numpy-accelerated if available)
        scores = _batch_cosine_similarity(source_vec, embeddings)
        scored = list(zip(scores, row_dicts))
        scored.sort(key=lambda x: x[0], reverse=True)

        sl = self._config.snippet_length
        result: List[Memory] = []
        for score, r_dict in scored[:limit]:
            if score < 0.2:
                break
            # content excluded from query — use short_summary as lightweight placeholder
            if "content" not in r_dict:
                r_dict["content"] = r_dict.get("short_summary", "")
            mem = Memory.from_row(r_dict)
            mem.snippet = mem.get_snippet(sl)
            result.append(mem)
        return result

    # ── Versioning ────────────────────────────────────────────────────────

    def get_versions(self, key: str, namespace: str = "default") -> List[Version]:
        rows = self._conn.execute(
            "SELECT * FROM memory_versions WHERE namespace = ? AND key = ? ORDER BY version DESC",
            (namespace, key),
        ).fetchall()
        return [Version.from_row(dict(row)) for row in rows]

    def restore_version(self, key: str, namespace: str = "default",
                        version: int = 1) -> Optional[Memory]:
        row = self._conn.execute(
            "SELECT * FROM memory_versions WHERE namespace = ? AND key = ? AND version = ?",
            (namespace, key, version),
        ).fetchone()
        if not row:
            return None

        row_dict = dict(row)
        tags = [t for t in row_dict["tags"].split(",") if t] if row_dict["tags"] else []
        return self.store(key, row_dict["content"], tags, row_dict["title"], namespace)

    # ── Export / Import / Stats ───────────────────────────────────────────

    def list_namespaces(self) -> List[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT namespace FROM memories ORDER BY namespace"
        ).fetchall()
        return [row[0] for row in rows]

    def get_stats(self) -> StorageStats:
        conn = self._conn
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        chars = conn.execute("SELECT COALESCE(SUM(chars), 0) FROM memories").fetchone()[0]
        ns = conn.execute("SELECT COUNT(DISTINCT namespace) FROM memories").fetchone()[0]
        size = round(self._db_path.stat().st_size / 1024, 1) if self._db_path.exists() else 0
        return StorageStats(
            total_memories=total,
            total_chars=chars,
            namespaces=ns,
            db_size_kb=size,
            db_path=str(self._db_path),
        )

    def export_all(self) -> List[Memory]:
        return self.list_all()[0]

    def import_all(self, memories: List[dict]) -> int:
        """Import memories from dicts. Delegates to bulk_store."""
        return self.bulk_store(memories)

    def migrate_from_json(self, json_dir: str) -> int:
        """Migrate memories from ContextKeep JSON files to SQLite."""
        json_path = Path(json_dir)
        if not json_path.exists():
            return 0

        count = 0
        for f in json_path.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                self.store(
                    data["key"],
                    data.get("content", ""),
                    data.get("tags", []),
                    data.get("title", data["key"]),
                    data.get("namespace", "default"),
                )
                count += 1
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                logger.warning("Migration skipped %s: %s", f.name, e)
        return count
