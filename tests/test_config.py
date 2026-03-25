import pytest

from core.config import NVCConfig


def test_default_config():
    cfg = NVCConfig()
    assert cfg.db_path == "./data/nvc.db"
    assert cfg.mcp_host == "127.0.0.1"
    assert cfg.mcp_port == 9998
    assert cfg.transport == "stdio"
    assert cfg.auth_enabled is False
    assert cfg.max_content_length == 1_000_000
    assert cfg.max_versions_kept == 5
    assert cfg.search_result_limit == 50


def test_from_env(monkeypatch):
    monkeypatch.setenv("NVC_DB_PATH", "/tmp/custom.db")
    monkeypatch.setenv("NVC_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("NVC_MCP_PORT", "9999")
    monkeypatch.setenv("NVC_API_KEY", "secret123")

    cfg = NVCConfig.from_env()
    assert cfg.db_path == "/tmp/custom.db"
    assert cfg.mcp_host == "0.0.0.0"
    assert cfg.mcp_port == 9999
    assert cfg.api_key == "secret123"


def test_remote_homelab_defaults_to_sse(monkeypatch):
    monkeypatch.setenv("NVC_PROFILE", "remote-homelab")
    monkeypatch.setenv("NVC_API_KEY", "nvc_" + "a" * 48)

    cfg = NVCConfig.from_env()
    assert cfg.transport == "sse"
    assert cfg.auth_enabled is True


def test_from_env_normalizes_http_transport_alias(monkeypatch):
    monkeypatch.setenv("NVC_TRANSPORT", "http")

    cfg = NVCConfig.from_env()
    assert cfg.transport == "sse"


def test_validate_valid():
    cfg = NVCConfig()
    cfg.validate()


def test_validate_invalid_port_zero():
    cfg = NVCConfig(mcp_port=0)
    with pytest.raises(ValueError, match="Invalid port"):
        cfg.validate()


def test_validate_invalid_port_too_high():
    cfg = NVCConfig(mcp_port=99999)
    with pytest.raises(ValueError, match="Invalid port"):
        cfg.validate()


def test_validate_invalid_content_length():
    cfg = NVCConfig(max_content_length=0)
    with pytest.raises(ValueError, match="max_content_length must be positive"):
        cfg.validate()


def test_snippet_length_default():
    cfg = NVCConfig()
    assert cfg.snippet_length == 250


def test_from_env_all_fields(monkeypatch):
    monkeypatch.setenv("NVC_DB_PATH", "/tmp/custom.db")
    monkeypatch.setenv("NVC_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("NVC_MCP_PORT", "8080")
    monkeypatch.setenv("NVC_API_KEY", "testkey")
    monkeypatch.setenv("NVC_SNIPPET_LENGTH", "100")
    monkeypatch.setenv("NVC_MAX_CONTENT_LENGTH", "500000")
    monkeypatch.setenv("NVC_SEARCH_LIMIT", "25")
    monkeypatch.setenv("NVC_MAX_VERSIONS_KEPT", "10")
    monkeypatch.setenv("NVC_MAX_KEY_LENGTH", "128")
    monkeypatch.setenv("NVC_MAX_TITLE_LENGTH", "256")
    monkeypatch.setenv("NVC_MAX_TAGS_LENGTH", "2048")

    cfg = NVCConfig.from_env()
    assert cfg.db_path == "/tmp/custom.db"
    assert cfg.mcp_host == "0.0.0.0"
    assert cfg.mcp_port == 8080
    assert cfg.api_key == "testkey"
    assert cfg.snippet_length == 100
    assert cfg.max_content_length == 500000
    assert cfg.search_result_limit == 25
    assert cfg.max_versions_kept == 10
    assert cfg.max_key_length == 128
    assert cfg.max_title_length == 256
    assert cfg.max_tags_length == 2048


def test_validate_invalid_api_key():
    cfg = NVCConfig(api_key="bad_key_without_prefix_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    with pytest.raises(ValueError, match="api_key must start with 'nvc_'"):
        cfg.validate()


def test_validate_invalid_versions_kept():
    cfg = NVCConfig(max_versions_kept=0)
    with pytest.raises(ValueError, match="max_versions_kept must be positive"):
        cfg.validate()


def test_validate_invalid_search_limit():
    cfg = NVCConfig(search_result_limit=0)
    with pytest.raises(ValueError, match="search_result_limit must be positive"):
        cfg.validate()


def test_validate_invalid_snippet_length():
    cfg = NVCConfig(snippet_length=0)
    with pytest.raises(ValueError, match="snippet_length must be positive"):
        cfg.validate()


def test_validate_invalid_transport():
    cfg = NVCConfig(transport="http")
    with pytest.raises(ValueError, match="transport must be one of"):
        cfg.validate()
