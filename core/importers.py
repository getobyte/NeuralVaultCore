# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Importers — Notion, Obsidian, Markdown, Plain Text
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import logging
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    """Convert text to a URL-safe key."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return slug.strip("-")[:200] or "untitled"


def _extract_frontmatter(content: str) -> tuple:
    """Extract YAML frontmatter from markdown. Returns (metadata_dict, body)."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, parts[2].strip()


def import_markdown_files(
    directory: str,
    namespace: str = "imported:markdown",
) -> List[dict]:
    """
    Import .md files from a directory.
    Extracts frontmatter for metadata, uses filename as key.
    Returns list of memory dicts ready for storage.store().
    """
    path = Path(directory)
    if not path.is_dir():
        raise ValueError(f"Directory not found: {directory}")

    memories = []
    for f in sorted(path.rglob("*.md")):
        try:
            raw = f.read_text(encoding="utf-8")
            meta, body = _extract_frontmatter(raw)

            # Use relative path as key
            rel_path = f.relative_to(path)
            key = _slugify(str(rel_path).replace(".md", ""))
            title = meta.get(
                "title", f.stem.replace("-", " ").replace("_", " ").title()
            )
            tags_str = meta.get("tags", "")
            tags = [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
            if not tags:
                tags = ["markdown", "imported"]

            memories.append(
                {
                    "key": key,
                    "content": body or raw,
                    "title": title[:512],
                    "namespace": namespace,
                    "tags": tags,
                }
            )
        except Exception as e:
            logger.warning("Skipped %s: %s", f.name, e)

    return memories


def import_obsidian_vault(
    vault_path: str,
    namespace: str = "imported:obsidian",
) -> List[dict]:
    """
    Import an Obsidian vault (directory of .md files).
    Handles: frontmatter, wikilinks (stripped), tags from frontmatter or inline #tags.
    """
    path = Path(vault_path)
    if not path.is_dir():
        raise ValueError(f"Vault not found: {vault_path}")

    memories = []
    for f in sorted(path.rglob("*.md")):
        # Skip Obsidian system files
        rel = f.relative_to(path)
        if any(part.startswith(".") for part in rel.parts):
            continue

        try:
            raw = f.read_text(encoding="utf-8")
            meta, body = _extract_frontmatter(raw)

            # Extract inline tags (#tag)
            inline_tags = re.findall(r"(?:^|\s)#([a-zA-Z0-9_/-]+)", body)

            # Clean wikilinks [[link]] -> link, [[link|alias]] -> alias
            body = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", body)

            key = _slugify(str(rel).replace(".md", ""))
            title = meta.get(
                "title", f.stem.replace("-", " ").replace("_", " ").title()
            )

            tags_str = meta.get("tags", "")
            tags = [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
            tags.extend(inline_tags[:10])
            if not tags:
                tags = ["obsidian"]
            tags = list(dict.fromkeys(tags))  # deduplicate preserving order

            # Use folder structure as extra context
            folder = str(rel.parent) if str(rel.parent) != "." else ""
            if folder:
                tags.append(f"folder:{folder}")

            memories.append(
                {
                    "key": key,
                    "content": body or raw,
                    "title": title[:512],
                    "namespace": namespace,
                    "tags": tags,
                }
            )
        except Exception as e:
            logger.warning("Skipped %s: %s", f.name, e)

    return memories


def import_notion_export(
    export_path: str,
    namespace: str = "imported:notion",
) -> List[dict]:
    """
    Import from Notion export (ZIP or extracted directory).
    Notion exports contain markdown files + CSV files.
    Handles: nested folders, CSV tables, markdown content.
    """
    path = Path(export_path)
    tmpdir: str | None = None

    # If ZIP, extract to temp
    if path.suffix.lower() == ".zip":
        tmpdir = tempfile.mkdtemp(prefix="nvc-notion-")
        try:
            with zipfile.ZipFile(path) as zf:
                zf.extractall(tmpdir)
        except Exception as e:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise
        path = Path(tmpdir)
        logger.info("Extracted Notion ZIP to %s", tmpdir)

    try:
        if not path.is_dir():
            raise ValueError(f"Path not found: {export_path}")

        memories = []

        # Import markdown files
        for f in sorted(path.rglob("*.md")):
            try:
                raw = f.read_text(encoding="utf-8")
                rel = f.relative_to(path)

                # Notion filenames often have UUID suffixes, clean them
                name = re.sub(r"\s+[a-f0-9]{32}$", "", f.stem)
                key = f"notion-{_slugify(str(rel).replace('.md', ''))}"
                title = name.replace("-", " ").replace("_", " ").title()

                # Detect folder as category
                folder = str(rel.parent)
                tags = ["notion"]
                if folder and folder != ".":
                    tags.append(f"section:{folder}")

                memories.append(
                    {
                        "key": key,
                        "content": raw.strip(),
                        "title": title[:512],
                        "namespace": namespace,
                        "tags": tags,
                    }
                )
            except Exception as e:
                logger.warning("Skipped %s: %s", f.name, e)

        # Import CSV files as structured data
        for f in sorted(path.rglob("*.csv")):
            try:
                raw = f.read_text(encoding="utf-8")
                rel = f.relative_to(path)
                name = re.sub(r"\s+[a-f0-9]{32}$", "", f.stem)
                key = f"notion-csv-{_slugify(str(rel).replace('.csv', ''))}"

                memories.append(
                    {
                        "key": key,
                        "content": raw.strip(),
                        "title": f"{name} (table)"[:512],
                        "namespace": namespace,
                        "tags": ["notion", "csv", "table"],
                    }
                )
            except Exception as e:
                logger.warning("Skipped %s: %s", f.name, e)

        return memories
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def import_plain_text(
    file_path: str,
    namespace: str = "imported:text",
    separator: str = "---",
) -> List[dict]:
    """
    Import from a plain text file. Splits by separator (default ---).
    Each block becomes a memory. First line = title.
    """
    path = Path(file_path)
    if not path.is_file():
        raise ValueError(f"File not found: {file_path}")

    raw = path.read_text(encoding="utf-8")
    blocks = re.split(rf"\n{re.escape(separator)}\n", raw)

    memories = []
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
        lines = block.split("\n", 1)
        title = lines[0].lstrip("# ").strip()[:512]
        key = _slugify(title) or f"text-{i}"

        memories.append(
            {
                "key": key,
                "content": block,
                "title": title,
                "namespace": namespace,
                "tags": ["imported", "text"],
            }
        )

    return memories


def import_json_file(
    file_path: str,
    namespace: str = "imported:json",
) -> List[dict]:
    """
    Import from JSON file. Supports:
    - NVC export format: {"memories": [...]}
    - Array of objects: [{"key": ..., "content": ...}, ...]
    - Single object: {"key": ..., "content": ...}
    """
    path = Path(file_path)
    if not path.is_file():
        raise ValueError(f"File not found: {file_path}")

    raw = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and "memories" in raw:
        items = raw["memories"]
    elif isinstance(raw, dict) and "key" in raw:
        items = [raw]
    else:
        raise ValueError("Unrecognized JSON format")

    memories = []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = item.get("key", "").strip()
        content = item.get("content", "").strip()
        if not key or not content:
            continue
        memories.append(
            {
                "key": key,
                "content": content,
                "title": item.get("title", key)[:512],
                "namespace": item.get("namespace", namespace),
                "tags": item.get("tags", ["imported"]),
            }
        )

    return memories
