# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Data models — typed dataclasses for Memory, Version, Stats
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Memory:
    """A single memory entry."""

    key: str
    content: str
    namespace: str = "default"
    title: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    chars: int = 0
    lines: int = 0
    snippet: str = ""

    def __post_init__(self) -> None:
        if not self.title:
            self.title = self.key
        if not self.chars:
            self.chars = len(self.content)
        if not self.lines:
            self.lines = self.content.count("\n") + 1

    @property
    def tags_str(self) -> str:
        return ",".join(self.tags)

    @staticmethod
    def parse_tags(tags: str) -> List[str]:
        """Parse comma-separated tag string into a clean list."""
        if not tags:
            return []
        return [t.strip() for t in tags.split(",") if t.strip()]

    def get_snippet(self, length: int = 250) -> str:
        """Return truncated content with ellipsis if needed."""
        if len(self.content) > length:
            return self.content[:length] + "\u2026"
        return self.content

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "key": self.key,
            "title": self.title,
            "content": self.content,
            "namespace": self.namespace,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "chars": self.chars,
            "lines": self.lines,
        }

    @classmethod
    def from_row(cls, row: dict) -> Memory:
        """Construct from a sqlite3.Row dict."""
        tags_raw = row.get("tags", "")
        tags = [t for t in tags_raw.split(",") if t] if isinstance(tags_raw, str) else tags_raw
        return cls(
            key=row["key"],
            content=row["content"],
            namespace=row.get("namespace", "default"),
            title=row.get("title", row["key"]),
            tags=tags,
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
            chars=row.get("chars", len(row["content"])),
            lines=row.get("lines", 0),
        )


@dataclass
class Version:
    """A versioned snapshot of a memory."""

    key: str
    version: int
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    namespace: str = "default"
    saved_at: str = ""

    @property
    def tags_str(self) -> str:
        return ",".join(self.tags)

    @classmethod
    def from_row(cls, row: dict) -> Version:
        tags_raw = row.get("tags", "")
        tags = [t for t in tags_raw.split(",") if t] if isinstance(tags_raw, str) else tags_raw
        return cls(
            key=row["key"],
            version=row["version"],
            title=row["title"],
            content=row["content"],
            tags=tags,
            namespace=row.get("namespace", "default"),
            saved_at=row.get("saved_at", ""),
        )


@dataclass
class StorageStats:
    """Storage statistics."""

    total_memories: int = 0
    total_chars: int = 0
    namespaces: int = 0
    db_size_kb: float = 0.0
    db_path: str = ""
