# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Centralized configuration — env loading, defaults, validation
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ── Well-known constants ──
DEFAULT_NAMESPACE = "default"
STATE_KEY = "_state"

PROFILE_DEFAULTS = {
    "local-stdio": {
        "transport": "stdio",
        "auth_enabled": False,
        "mcp_host": "127.0.0.1",
        "mcp_port": 9998,
        "ui_host": "127.0.0.1",
        "ui_port": 9999,
    },
    "local-ui": {
        "transport": "stdio",
        "auth_enabled": False,
        "mcp_host": "127.0.0.1",
        "mcp_port": 9998,
        "ui_host": "127.0.0.1",
        "ui_port": 9999,
    },
    "remote-homelab": {
        "transport": "sse",
        "auth_enabled": True,
        "mcp_host": "0.0.0.0",
        "mcp_port": 9998,
        "ui_host": "0.0.0.0",
        "ui_port": 9999,
    },
}


@dataclass(frozen=True)
class NVCConfig:
    """Immutable configuration for NeuralVaultCore."""

    # Profile
    profile: str = "local-stdio"

    # Storage
    db_path: str = "./data/nvc.db"

    # Server
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 9998
    transport: str = "stdio"

    # Auth
    api_key: str = ""
    auth_enabled: bool = False

    # UI
    ui_host: str = "127.0.0.1"
    ui_port: int = 9999

    # Limits
    max_key_length: int = 256
    max_title_length: int = 512
    max_content_length: int = 1_000_000  # 1 MB
    max_tags_length: int = 1_024
    max_versions_kept: int = 5
    search_result_limit: int = 50
    snippet_length: int = 250

    # Observability
    log_tokens: bool = False

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> NVCConfig:
        """Load config from environment variables. Optionally load .env first."""
        if env_file and env_file.exists():
            _load_env_file(env_file)

        profile_name = os.getenv("NVC_PROFILE", "local-stdio")
        profile = PROFILE_DEFAULTS.get(profile_name, PROFILE_DEFAULTS["local-stdio"])
        transport = _normalize_transport(
            os.getenv("NVC_TRANSPORT", profile["transport"])
        )

        return cls(
            profile=profile_name,
            db_path=os.getenv("NVC_DB_PATH", "./data/nvc.db"),
            mcp_host=os.getenv(
                "NVC_HOST", os.getenv("NVC_MCP_HOST", profile["mcp_host"])
            ),
            mcp_port=int(
                os.getenv(
                    "NVC_PORT", os.getenv("NVC_MCP_PORT", str(profile["mcp_port"]))
                )
            ),
            transport=transport,
            api_key=os.getenv("NVC_API_KEY", "").strip(),
            auth_enabled=os.getenv("NVC_AUTH", str(profile["auth_enabled"])).lower()
            in ("true", "1", "yes"),
            ui_host=os.getenv("NVC_UI_HOST", profile["ui_host"]),
            ui_port=int(os.getenv("NVC_UI_PORT", str(profile["ui_port"]))),
            snippet_length=int(os.getenv("NVC_SNIPPET_LENGTH", "250")),
            max_content_length=int(os.getenv("NVC_MAX_CONTENT_LENGTH", "1000000")),
            search_result_limit=int(os.getenv("NVC_SEARCH_LIMIT", "50")),
            max_versions_kept=int(os.getenv("NVC_MAX_VERSIONS_KEPT", "5")),
            max_key_length=int(os.getenv("NVC_MAX_KEY_LENGTH", "256")),
            max_title_length=int(os.getenv("NVC_MAX_TITLE_LENGTH", "512")),
            max_tags_length=int(os.getenv("NVC_MAX_TAGS_LENGTH", "1024")),
            log_tokens=os.getenv("NVC_LOG_TOKENS", "").lower() in ("true", "1", "yes"),
        )

    def validate(self) -> None:
        """Raise ValueError if config is invalid."""
        if self.profile not in ("local-stdio", "local-ui", "remote-homelab"):
            raise ValueError(
                f"Unknown profile: {self.profile}. Use: local-stdio, local-ui, remote-homelab"
            )
        if self.profile == "remote-homelab" and not self.api_key:
            raise ValueError("remote-homelab profile requires NVC_API_KEY to be set")
        if self.transport not in ("stdio", "sse"):
            raise ValueError("transport must be one of: stdio, sse")
        if self.mcp_port < 1 or self.mcp_port > 65535:
            raise ValueError(f"Invalid port: {self.mcp_port}")
        if self.max_content_length < 1:
            raise ValueError("max_content_length must be positive")
        if self.api_key:
            if not self.api_key.startswith("nvc_") or len(self.api_key) != 52:
                raise ValueError(
                    "api_key must start with 'nvc_' and be exactly 52 characters"
                )
        if self.max_versions_kept <= 0:
            raise ValueError("max_versions_kept must be positive")
        if self.search_result_limit <= 0:
            raise ValueError("search_result_limit must be positive")
        if self.snippet_length <= 0:
            raise ValueError("snippet_length must be positive")


def _normalize_transport(value: str) -> str:
    transport = (value or "stdio").strip().lower()
    if transport == "http":
        return "sse"
    return transport


def _load_env_file(path: Path) -> None:
    """Load .env file into os.environ. Uses python-dotenv if available, fallback to manual."""
    try:
        from dotenv import load_dotenv

        load_dotenv(path)
    except ImportError:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            os.environ.setdefault(key.strip(), value)
