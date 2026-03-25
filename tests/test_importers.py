import json
import zipfile
import pytest
from core.importers import (
    import_markdown_files,
    import_notion_export,
    import_plain_text,
    import_json_file,
    _slugify,
    _extract_frontmatter,
)


def test_slugify():
    assert _slugify("Hello World!") == "hello-world"
    assert _slugify("test_file-name") == "test-file-name"
    assert _slugify("") == "untitled"


def test_extract_frontmatter():
    content = "---\ntitle: Test\ntags: a, b\n---\nBody here"
    meta, body = _extract_frontmatter(content)
    assert meta["title"] == "Test"
    assert body == "Body here"


def test_extract_frontmatter_no_frontmatter():
    meta, body = _extract_frontmatter("Just plain text")
    assert meta == {}
    assert body == "Just plain text"


def test_import_markdown_files(tmp_path):
    (tmp_path / "note1.md").write_text("---\ntitle: Note One\n---\nContent one", encoding="utf-8")
    (tmp_path / "note2.md").write_text("# Note Two\n\nContent two", encoding="utf-8")
    memories = import_markdown_files(str(tmp_path))
    assert len(memories) == 2
    assert any(m["title"] == "Note One" for m in memories)


def test_import_plain_text(tmp_path):
    txt = "First block\nSome content\n---\nSecond block\nMore content"
    f = tmp_path / "notes.txt"
    f.write_text(txt, encoding="utf-8")
    memories = import_plain_text(str(f))
    assert len(memories) == 2
    assert memories[0]["title"] == "First block"


def test_import_json_file_array(tmp_path):
    data = [{"key": "k1", "content": "c1"}, {"key": "k2", "content": "c2"}]
    f = tmp_path / "data.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    memories = import_json_file(str(f))
    assert len(memories) == 2


def test_import_json_file_nvc_format(tmp_path):
    data = {"memories": [{"key": "k1", "content": "c1", "title": "T1"}], "count": 1}
    f = tmp_path / "export.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    memories = import_json_file(str(f))
    assert len(memories) == 1
    assert memories[0]["title"] == "T1"


def test_import_markdown_nonexistent():
    with pytest.raises(ValueError):
        import_markdown_files("/nonexistent/path")


def test_import_notion_zip_cleans_tempdir_on_success(tmp_path, monkeypatch):
    zip_path = tmp_path / "notion.zip"
    tracked_tmpdir = tmp_path / "tracked-temp"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("Notes/Project Plan.md", "# Plan")

    def _mkdtemp(prefix):
        tracked_tmpdir.mkdir()
        return str(tracked_tmpdir)

    monkeypatch.setattr("core.importers.tempfile.mkdtemp", _mkdtemp)

    memories = import_notion_export(str(zip_path))

    assert memories
    assert tracked_tmpdir.exists() is False


def test_import_notion_zip_cleans_tempdir_on_error(tmp_path, monkeypatch):
    zip_path = tmp_path / "broken.zip"
    tracked_tmpdir = tmp_path / "tracked-temp-error"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("Notes/Project Plan.md", "# Plan")

    def _mkdtemp(prefix):
        tracked_tmpdir.mkdir()
        return str(tracked_tmpdir)

    monkeypatch.setattr("core.importers.tempfile.mkdtemp", _mkdtemp)
    monkeypatch.setattr("core.importers.zipfile.ZipFile.extractall", lambda self, path: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(RuntimeError, match="boom"):
        import_notion_export(str(zip_path))

    assert tracked_tmpdir.exists() is False
