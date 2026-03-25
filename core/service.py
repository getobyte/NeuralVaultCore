# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Service layer — shared business logic for MCP, CLI, UI
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
from typing import List, Optional

from core.config import NVCConfig
from core.models import Memory, StorageStats, Version
from core.storage import SQLiteStorage

logger = logging.getLogger(__name__)


class MemoryService:
    """Shared business logic. MCP, CLI, and UI all use this."""

    def __init__(self, storage: SQLiteStorage) -> None:
        self._storage = storage

    @property
    def config(self) -> NVCConfig:
        return self._storage.config

    # ── Store ──

    def store(self, key: str, content: str, tags: List[str],
              title: str = "", namespace: str = "default") -> Memory:
        return self._storage.store(key, content, tags, title, namespace)

    # ── Retrieve ──

    def retrieve(self, key: str, namespace: str = "default") -> Optional[Memory]:
        return self._storage.retrieve(key, namespace)

    # ── Search ──

    def search(self, query: str, namespace: Optional[str] = None,
               limit: int = 10) -> List[Memory]:
        results = self._storage.search(query, namespace)
        return results[:limit]

    # ── List ──

    def list_memories(self, namespace: Optional[str] = None,
                      limit: int = 20, offset: int = 0) -> tuple:
        return self._storage.list_all(namespace, limit, offset)

    def list_recent(self, limit: int = 10) -> List[Memory]:
        return self._storage.list_recent(limit)

    # ── Delete ──

    def delete(self, key: str, namespace: str = "default") -> bool:
        return self._storage.delete(key, namespace)

    # ── Context (with _state priority) ──

    def get_context(self, namespace: str, limit: int = 10) -> tuple:
        """Get context: _state first (if exists), then recent memories."""
        state = self._storage.retrieve("_state", namespace)
        memories, total = self._storage.list_all(namespace, limit=limit + 1)
        # Filter out _state from the list
        non_state = [m for m in memories if m.key != "_state"][:limit]
        return state, non_state, total

    # ── Versions ──

    def get_versions(self, key: str, namespace: str = "default") -> List[Version]:
        return self._storage.get_versions(key, namespace)

    def restore_version(self, key: str, namespace: str = "default",
                        version: int = 1) -> Optional[Memory]:
        return self._storage.restore_version(key, namespace, version)

    # ── Stats ──

    def get_stats(self) -> StorageStats:
        return self._storage.get_stats()

    # ── Namespaces ──

    def list_namespaces(self) -> List[str]:
        return self._storage.list_namespaces()

    # ── Bulk operations (CLI-only) ──

    def bulk_store(self, memories: list) -> int:
        return self._storage.bulk_store(memories)

    def search_similar(self, key: str, namespace: str = "default",
                       limit: int = 10) -> List[Memory]:
        return self._storage.search_similar(key, namespace, limit)

    def export_all(self) -> List[Memory]:
        return self._storage.export_all()

    def import_all(self, memories: list) -> int:
        return self._storage.import_all(memories)

    def migrate_from_json(self, json_dir: str) -> int:
        return self._storage.migrate_from_json(json_dir)

    # ── Compact formatters (for MCP output) ──

    @staticmethod
    def format_compact_memory(mem: Memory, include_content: bool = False) -> str:
        """Pipe-delimited compact format for MCP output."""
        tags = ",".join(mem.tags) or "-"
        line = f"{mem.key} | {mem.title} | {mem.namespace} | {tags} | {mem.updated_at[:16]}"
        if include_content:
            line += f"\n\n{mem.content}"
        return line

    @staticmethod
    def format_compact_list(memories: List[Memory], total: int, offset: int = 0) -> str:
        """Compact list format for MCP output."""
        if not memories:
            return "0 memories"
        header = f"{len(memories)}/{total} memories"
        if offset > 0:
            header += f" (offset {offset})"
        lines = [header]
        for mem in memories:
            tags = ",".join(mem.tags) or "-"
            lines.append(f"{mem.key} | {mem.title} | {mem.namespace} | {tags} | {mem.updated_at[:16]}")
        return "\n".join(lines)

    @staticmethod
    def format_not_found(key: str, namespace: str = "default") -> str:
        """Actionable not-found message."""
        return f"not_found | {key} | ns:{namespace} | try search_memories or list_all_memories"
