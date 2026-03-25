# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Authentication — API key generation, validation, middleware
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import logging
import secrets
from typing import TYPE_CHECKING

from core.exceptions import NVCAuthError

if TYPE_CHECKING:
    from core.config import NVCConfig

logger = logging.getLogger(__name__)

API_KEY_PREFIX = "nvc_"
API_KEY_BYTES = 24  # 48 hex chars


def generate_api_key() -> str:
    """Generate a new NVC API key with prefix."""
    return API_KEY_PREFIX + secrets.token_hex(API_KEY_BYTES)


def verify_api_key(provided: str, expected: str) -> bool:
    """Constant-time comparison of API keys. Returns False if either is empty."""
    if not provided or not expected:
        return False
    return secrets.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))


def build_auth_middleware(config: NVCConfig):
    """
    Build FastMCP native Middleware for Bearer token auth.
    Returns None if FastMCP middleware is unavailable.
    """
    try:
        from fastmcp.server.middleware import Middleware, MiddlewareContext
        from fastmcp.server.dependencies import get_http_request
    except ImportError:
        logger.warning(
            "FastMCP middleware not available (need fastmcp>=2.9). "
            "SSE auth DISABLED — upgrade: pip install 'fastmcp>=2.9'"
        )
        return None

    expected_key = config.api_key

    class NVCAuthMiddleware(Middleware):
        """Verify Bearer token on every MCP operation over HTTP transport."""

        async def _check_auth(self, context: MiddlewareContext, call_next):
            if not config.auth_enabled:
                return await call_next(context)

            try:
                request = get_http_request()
            except Exception as e:
                # stdio transport — no HTTP request available, skip auth
                return await call_next(context)

            if request is None:
                return await call_next(context)

            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                raise NVCAuthError(
                    "Unauthorized: Missing header Authorization: Bearer <api_key>"
                )

            token = auth_header[7:]
            if not verify_api_key(token, expected_key):
                raise NVCAuthError("Forbidden: Invalid API key")

            return await call_next(context)

        async def on_call_tool(self, context, call_next):
            return await self._check_auth(context, call_next)

        async def on_list_tools(self, context, call_next):
            return await self._check_auth(context, call_next)

        async def on_list_resources(self, context, call_next):
            return await self._check_auth(context, call_next)

    return NVCAuthMiddleware()
