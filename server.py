# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# MCP Server — tool definitions + auth middleware (thin wiring)
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Optional

from core.config import NVCConfig
from core.auth import build_auth_middleware
from core.models import Memory
from core.storage import SQLiteStorage
from core.service import MemoryService

# Logging ALWAYS on stderr — stdout stays clean for MCP stdio
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [NVC] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Structured JSON logging (opt-in via NVC_LOG_JSON=true) ──
if os.getenv("NVC_LOG_JSON", "").lower() in ("true", "1", "yes"):
    import json as _json

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            return _json.dumps(
                {
                    "ts": self.formatTime(record),
                    "level": record.levelname,
                    "msg": record.getMessage(),
                    "module": record.module,
                }
            )

    for handler in logging.root.handlers:
        handler.setFormatter(JSONFormatter())


# ──────────────────────────────────────────────────────────────────────────────
# Lazy service singleton — initialized at startup, not import time
# ──────────────────────────────────────────────────────────────────────────────

_service: Optional[MemoryService] = None


def _get_service() -> MemoryService:
    if _service is None:
        raise RuntimeError("Service not initialized.")
    return _service


def _init_service(config: NVCConfig) -> MemoryService:
    global _service
    storage = SQLiteStorage(config)
    _service = MemoryService(storage)
    return _service


# ──────────────────────────────────────────────────────────────────────────────
# FastMCP instance builder
# ──────────────────────────────────────────────────────────────────────────────


def _import_fastmcp():
    """Import FastMCP with fallback between fastmcp and mcp.server.fastmcp."""
    try:
        from fastmcp import FastMCP

        return FastMCP
    except (ImportError, Exception):
        from mcp.server.fastmcp import FastMCP

        return FastMCP


def _create_mcp(config: NVCConfig):
    """Create FastMCP instance with optional auth middleware."""
    FastMCP = _import_fastmcp()

    middleware_list = []
    if config.auth_enabled:
        mw = build_auth_middleware(config)
        if mw:
            middleware_list.append(mw)

    try:
        mcp = FastMCP("neural-vault-core", middleware=middleware_list)
    except TypeError:
        logger.warning(
            "FastMCP does not support middleware param — SSE auth unavailable"
        )
        mcp = FastMCP("neural-vault-core")

    _register_tools(mcp)
    _register_health(mcp)
    return mcp


# ──────────────────────────────────────────────────────────────────────────────
# Health endpoint — no auth required
# ──────────────────────────────────────────────────────────────────────────────


def _register_health(mcp) -> None:
    from starlette.responses import JSONResponse

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        return JSONResponse({"status": "ok", "version": "1.0.0"})


# ──────────────────────────────────────────────────────────────────────────────
# MCP Tools — thin wrappers that delegate to service layer
# ──────────────────────────────────────────────────────────────────────────────


def _estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token)."""
    return max(1, len(text) // 4)


def _log_tokens(tool_name: str, response: str) -> str:
    """Log estimated token count for a tool response."""
    config = _service.config if _service else None
    if config and config.log_tokens:
        tokens = _estimate_tokens(response)
        logger.info(
            "TOKEN_USAGE %s: ~%d tokens (%d chars)", tool_name, tokens, len(response)
        )
    return response


# ── Request counting ──
_request_counts: Counter = Counter()


def _count_request(tool_name: str) -> None:
    """Increment request counter for a tool."""
    _request_counts[tool_name] += 1


def _register_tools(mcp) -> None:

    @mcp.tool()
    async def store_memory(
        key: str,
        content: str,
        tags: str = "",
        title: str = "",
        namespace: str = "default",
    ) -> str:
        """Store or update a memory. Auto-versions previous content."""
        _count_request("store_memory")
        logger.info("store_memory key=%s namespace=%s", key, namespace)
        try:
            tag_list = Memory.parse_tags(tags)
            mem = _get_service().store(key, content, tag_list, title, namespace)
            result = f"stored | {mem.key} | {mem.namespace} | {mem.chars} chars"
            return _log_tokens("store_memory", result)
        except ValueError as e:
            return f"error | {e}"

    @mcp.tool()
    async def retrieve_memory(
        key: str,
        namespace: str = "default",
        view: str = "head_tail",
        max_chars: int = 2000,
    ) -> str:
        """Get memory by key. view: head|tail|head_tail|full. max_chars limits output."""
        _count_request("retrieve_memory")
        logger.info("retrieve_memory key=%s namespace=%s view=%s", key, namespace, view)
        mem = _get_service().retrieve(key, namespace)
        if not mem:
            return f"not_found | {key} | ns:{namespace} | try search_memories or list_all_memories"
        tags = ",".join(mem.tags) or "-"
        header = f"{tags} | {mem.updated_at[:16]}"

        content = mem.content
        if view == "full" or len(content) <= max_chars:
            pass  # return full content
        elif view == "head":
            content = content[:max_chars]
            if len(mem.content) > max_chars:
                content += "\n...(truncated)"
        elif view == "tail":
            content = content[-max_chars:]
            if len(mem.content) > max_chars:
                content = "(truncated)...\n" + content
        else:  # head_tail
            half = max_chars // 2
            if len(content) > max_chars:
                content = content[:half] + "\n...(truncated)...\n" + content[-half:]

        result = f"{header}\n\n{content}"
        return _log_tokens("retrieve_memory", result)

    @mcp.tool()
    async def search_memories(
        query: str, namespace: str = "", keys_only: bool = True, limit: int = 10
    ) -> str:
        """Search memories. keys_only=True returns compact directory. 3+ words uses semantic search."""
        _count_request("search_memories")
        logger.info(
            "search_memories query=%s namespace=%s keys_only=%s limit=%d",
            query,
            namespace,
            keys_only,
            limit,
        )
        results = _get_service().search(query, namespace or None, limit)
        if not results:
            return f"0 results | {query}"
        lines = [f"{len(results)} results | {query}"]
        for mem in results:
            tags = ",".join(mem.tags) or "-"
            line = f"{mem.key} | {mem.title} | {mem.namespace} | {tags} | {mem.updated_at[:16]}"
            if not keys_only and mem.snippet:
                line += f" | {mem.snippet[:120]}"
            lines.append(line)
        return _log_tokens("search_memories", "\n".join(lines))

    @mcp.tool()
    async def list_all_memories(
        namespace: str = "", limit: int = 20, offset: int = 0, keys_only: bool = False
    ) -> str:
        """Paginated directory of all memories. keys_only=True returns only key|namespace pairs to save tokens."""
        _count_request("list_all_memories")
        logger.info(
            "list_all_memories namespace=%s limit=%d offset=%d keys_only=%s",
            namespace,
            limit,
            offset,
            keys_only,
        )
        memories, total = _get_service().list_memories(namespace or None, limit, offset)
        if keys_only:
            if not memories:
                return "0 memories"
            header = f"{len(memories)}/{total} memories"
            if offset > 0:
                header += f" (offset {offset})"
            lines = [header]
            for mem in memories:
                lines.append(f"{mem.key} | {mem.namespace}")
            result = "\n".join(lines)
        else:
            result = MemoryService.format_compact_list(memories, total, offset)
        return _log_tokens("list_all_memories", result)

    @mcp.tool()
    async def get_context(
        namespace: str, limit: int = 10, keys_only: bool = True
    ) -> str:
        """Get project context: _state first, then recent memories. keys_only=True (default) omits snippets to save tokens."""
        _count_request("get_context")
        logger.info(
            "get_context namespace=%s limit=%d keys_only=%s",
            namespace,
            limit,
            keys_only,
        )
        state, memories, total = _get_service().get_context(namespace, limit)
        lines = []
        if state:
            lines.append(f"_state | {state.updated_at[:16]} | {state.chars} chars")
            lines.append(state.content)
            lines.append("---")
        lines.append(f"{len(memories)}/{total} recent in {namespace}:")
        for mem in memories:
            tags = ",".join(mem.tags) or "-"
            line = f"{mem.key} | {mem.title} | {tags} | {mem.updated_at[:16]}"
            if not keys_only:
                snippet = mem.content[:200].replace("\n", " ")
                if len(mem.content) > 200:
                    snippet += "..."
                line += f" | {snippet}"
            lines.append(line)
        return _log_tokens("get_context", "\n".join(lines))

    @mcp.tool()
    async def delete_memory(key: str, namespace: str = "default") -> str:
        """Delete memory and all its versions."""
        _count_request("delete_memory")
        logger.info("delete_memory key=%s namespace=%s", key, namespace)
        if _get_service().delete(key, namespace):
            return f"deleted | {key} | ns:{namespace}"
        return f"not_found | {key} | ns:{namespace}"

    @mcp.tool()
    async def get_versions(key: str, namespace: str = "default") -> str:
        """List saved versions (max 5 kept)."""
        _count_request("get_versions")
        logger.info("get_versions key=%s namespace=%s", key, namespace)
        versions = _get_service().get_versions(key, namespace)
        if not versions:
            return f"no_versions | {key} | ns:{namespace}"
        lines = [f"{len(versions)} versions | {key}"]
        for v in versions:
            lines.append(f"v{v.version} | {v.saved_at[:16]} | {v.title}")
        return _log_tokens("get_versions", "\n".join(lines))

    @mcp.tool()
    async def restore_version(
        key: str, namespace: str = "default", version: int = 1
    ) -> str:
        """Restore a previous version. Current content is auto-versioned first."""
        _count_request("restore_version")
        logger.info(
            "restore_version key=%s namespace=%s version=%d", key, namespace, version
        )
        mem = _get_service().restore_version(key, namespace, version)
        if mem:
            return f"restored | {key} | v{version} | {mem.chars} chars"
        return f"not_found | {key} | v{version} | ns:{namespace}"

    @mcp.tool()
    async def get_stats(verbose: bool = False) -> str:
        """Storage statistics."""
        _count_request("get_stats")
        s = _get_service().get_stats()
        lines = [
            f"memories:{s.total_memories} | chars:{s.total_chars} | ns:{s.namespaces} | db:{s.db_size_kb}KB"
        ]
        if _request_counts:
            top = sorted(_request_counts.items(), key=lambda x: x[1], reverse=True)
            if not verbose:
                top = top[:5]
            for tool, count in top:
                lines.append(f"  {tool}: {count}")
        return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    env_file = Path(__file__).parent / ".env"
    base_config = NVCConfig.from_env(env_file if env_file.exists() else None)

    parser = argparse.ArgumentParser(description="NeuralVaultCore MCP Server v1.0")
    parser.add_argument(
        "--transport", choices=["stdio", "sse"], default=base_config.transport
    )
    parser.add_argument("--host", default=base_config.mcp_host)
    parser.add_argument("--port", type=int, default=base_config.mcp_port)
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable SSE auth (development only — DO NOT use in production)",
    )
    args = parser.parse_args()

    # Build final config with CLI overrides
    config = replace(
        base_config,
        mcp_host=args.host,
        mcp_port=args.port,
        transport=args.transport,
    )

    if args.no_auth and config.profile == "remote-homelab":
        logger.error("--no-auth is not allowed when NVC_PROFILE=remote-homelab")
        sys.exit(1)

    config.validate()

    # Initialize service
    _init_service(config)

    if args.transport == "sse":
        if not args.no_auth:
            if not config.api_key:
                logger.error("NVC_API_KEY not set — refusing to start SSE server.")
                logger.error("Set NVC_API_KEY in .env or use --no-auth for dev.")
                sys.exit(1)
            config = replace(config, auth_enabled=True)
            logger.info("SSE auth ENABLED — Bearer token required on every request")
        else:
            logger.warning("SSE auth DISABLED via --no-auth — NOT FOR PRODUCTION")

        logger.info(
            "Starting MCP SSE server on %s:%d", config.mcp_host, config.mcp_port
        )
        mcp = _create_mcp(config)
        mcp.run(transport="sse", host=config.mcp_host, port=config.mcp_port)
    else:
        logger.info("Starting MCP stdio server (auth not required for local transport)")
        mcp = _create_mcp(config)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
