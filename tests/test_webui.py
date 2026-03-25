from pathlib import Path

from starlette.testclient import TestClient

from core.config import NVCConfig
from core.storage import SQLiteStorage
import webui


def _make_client(tmp_path):
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html><body>spa shell</body></html>", encoding="utf-8")
    (dist_dir / "favicon.ico").write_bytes(b"ico-bytes")
    (dist_dir / "NVC-logo.png").write_bytes(b"png-bytes")
    (assets_dir / "index.js").write_text("console.log('ready')", encoding="utf-8")

    config = NVCConfig(db_path=str(tmp_path / "test.db"))
    webui._storage = SQLiteStorage(config)
    app = webui.create_app(dist_dir)
    return TestClient(app)


def test_api_memory_detail_uses_namespace_query(tmp_path):
    client = _make_client(tmp_path)
    storage = webui._storage
    storage.store("shared-key", "default content", [], "Default", "default")
    storage.store("shared-key", "project content", [], "Project", "project:alpha")

    response = client.get("/api/memories/shared-key?ns=project%3Aalpha")

    assert response.status_code == 200
    payload = response.json()
    assert payload["namespace"] == "project:alpha"
    assert payload["content"] == "project content"


def test_api_memory_delete_uses_namespace_query(tmp_path):
    client = _make_client(tmp_path)
    storage = webui._storage
    storage.store("shared-key", "default content", [], "Default", "default")
    storage.store("shared-key", "project content", [], "Project", "project:alpha")

    response = client.delete("/api/memories/shared-key?ns=project%3Aalpha")

    assert response.status_code == 200
    assert response.json()["namespace"] == "project:alpha"
    assert storage.retrieve("shared-key", "project:alpha") is None
    assert storage.retrieve("shared-key", "default") is not None


def test_root_static_assets_are_served_before_spa_fallback(tmp_path):
    client = _make_client(tmp_path)

    favicon = client.get("/favicon.ico")
    logo = client.get("/NVC-logo.png")
    spa = client.get("/memories/some-key")

    assert favicon.status_code == 200
    assert favicon.content == b"ico-bytes"
    assert logo.status_code == 200
    assert logo.content == b"png-bytes"
    assert spa.status_code == 200
    assert "spa shell" in spa.text


def test_invalid_json_returns_400_and_logs_warning(tmp_path, caplog):
    client = _make_client(tmp_path)
    caplog.set_level("WARNING")

    response = client.post("/api/memories", content="{", headers={"content-type": "application/json"})

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid JSON"
    assert "Invalid JSON for memory create" in caplog.text


def test_traversal_like_paths_return_404_instead_of_spa(tmp_path):
    client = _make_client(tmp_path)

    response = client.get("/..%2Fsecret.txt")

    assert response.status_code == 404
