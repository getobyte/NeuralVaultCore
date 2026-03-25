from pathlib import Path

import install


def test_generate_env_creates_valid_api_key(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("install.secrets.token_hex", lambda n: "a" * (n * 2))

    config = install.generate_env()
    env_text = Path(".env").read_text(encoding="utf-8")

    assert config["NVC_API_KEY"] == "nvc_" + ("a" * 48)
    assert len(config["NVC_API_KEY"]) == 52
    assert "NVC_API_KEY=nvc_" in env_text


def test_generate_env_keeps_existing_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("NVC_API_KEY=nvc_" + ("b" * 48) + "\n", encoding="utf-8")

    config = install.generate_env()

    assert config["NVC_API_KEY"] == "nvc_" + ("b" * 48)
