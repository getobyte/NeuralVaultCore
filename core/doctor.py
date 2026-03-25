# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Doctor — diagnostic and health checks
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
import logging
import os
import socket
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.config import NVCConfig

logger = logging.getLogger(__name__)


def run_doctor(config: NVCConfig) -> list:
    """Run all diagnostic checks. Returns list of (status, category, message) tuples."""
    results = []

    def ok(cat, msg):
        results.append(("OK", cat, msg))

    def warn(cat, msg):
        results.append(("WARN", cat, msg))

    def err(cat, msg):
        results.append(("ERROR", cat, msg))

    # Python version
    v = sys.version_info
    if v >= (3, 10):
        ok("python", f"Python {v.major}.{v.minor}.{v.micro}")
    else:
        err("python", f"Python {v.major}.{v.minor} — need 3.10+")

    # Core packages
    for pkg in ["fastmcp", "dotenv", "starlette", "uvicorn"]:
        try:
            importlib.import_module(pkg if pkg != "dotenv" else "dotenv")
            ok("packages", f"{pkg} installed")
        except ImportError:
            warn("packages", f"{pkg} not installed")

    # Semantic model
    try:
        import sentence_transformers

        ok("packages", "sentence-transformers installed")
    except ImportError:
        warn(
            "packages", "sentence-transformers not installed (semantic search disabled)"
        )

    # DB path
    db = Path(config.db_path)
    if db.exists():
        size = round(db.stat().st_size / 1024, 1)
        ok("database", f"DB exists: {db} ({size} KB)")
    else:
        if db.parent.exists():
            warn("database", f"DB not found: {db} (will be created on first use)")
        else:
            err("database", f"DB parent dir missing: {db.parent}")

    # Schema version
    if db.exists():
        try:
            import sqlite3

            conn = sqlite3.connect(str(db))
            from core.migration import get_schema_version, CURRENT_SCHEMA_VERSION

            v = get_schema_version(conn)
            conn.close()
            if v >= CURRENT_SCHEMA_VERSION:
                ok("schema", f"Schema version {v} (current)")
            elif v > 0:
                warn(
                    "schema",
                    f"Schema version {v} (needs migration to {CURRENT_SCHEMA_VERSION})",
                )
            else:
                warn("schema", "No schema_meta table (legacy DB)")
        except Exception as e:
            err("schema", f"Cannot check schema: {e}")

    # Profile
    ok("config", f"Profile: {config.profile}")
    ok("config", f"Transport: {config.transport}")

    # Auth
    if config.profile == "remote-homelab":
        if config.api_key:
            ok("auth", "API key set")
        else:
            err("auth", "remote-homelab requires NVC_API_KEY")
    else:
        ok("auth", f"Auth: {'enabled' if config.auth_enabled else 'disabled (local)'}")

    # Port check
    for port, label in [(config.mcp_port, "MCP"), (config.ui_port, "UI")]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.bind(("127.0.0.1", port))
            ok("ports", f"{label} port {port} available")
        except OSError:
            warn("ports", f"{label} port {port} in use")

    # UI assets
    dist = Path(__file__).parent.parent / "webui-dist"
    if dist.exists():
        ok("ui", f"UI assets: {dist}")
    else:
        warn("ui", "UI not built (run: cd 'NVC - BaseUI' && npm run build)")

    return results
