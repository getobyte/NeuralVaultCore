import pytest
from core.config import NVCConfig
from core.storage import SQLiteStorage
from core.service import MemoryService


@pytest.fixture
def service(tmp_path):
    config = NVCConfig(db_path=str(tmp_path / "test.db"))
    storage = SQLiteStorage(config)
    return MemoryService(storage)


def test_store_and_retrieve(service):
    mem = service.store("k1", "hello", ["t1"], "Title", "default")
    assert mem.key == "k1"
    retrieved = service.retrieve("k1", "default")
    assert retrieved is not None
    assert retrieved.content == "hello"


def test_retrieve_not_found(service):
    assert service.retrieve("nope", "default") is None


def test_search(service):
    service.store("k1", "the quick brown fox", [], "Fox", "default")
    results = service.search("fox")
    assert len(results) >= 1


def test_list_memories(service):
    for i in range(3):
        service.store(f"k{i}", f"content {i}", [], f"T{i}", "default")
    memories, total = service.list_memories()
    assert len(memories) == 3
    assert total == 3


def test_delete(service):
    service.store("k1", "content", [], "T", "default")
    assert service.delete("k1", "default") is True
    assert service.retrieve("k1", "default") is None


def test_get_context_with_state(service):
    service.store("_state", "current project state", ["state"], "_state", "project:foo")
    service.store("note1", "some note", [], "Note 1", "project:foo")
    service.store("note2", "another note", [], "Note 2", "project:foo")

    state, memories, total = service.get_context("project:foo", limit=10)
    assert state is not None
    assert state.key == "_state"
    assert state.content == "current project state"
    assert all(m.key != "_state" for m in memories)
    assert len(memories) == 2


def test_get_context_without_state(service):
    service.store("note1", "some note", [], "Note 1", "myns")
    state, memories, total = service.get_context("myns", limit=10)
    assert state is None
    assert len(memories) == 1


def test_versions(service):
    service.store("k1", "v1", [], "T", "default")
    service.store("k1", "v2", [], "T", "default")
    versions = service.get_versions("k1", "default")
    assert len(versions) == 1
    assert versions[0].content == "v1"


def test_format_compact_list(service):
    service.store("k1", "content", ["t1"], "Title", "default")
    memories, total = service.list_memories()
    output = MemoryService.format_compact_list(memories, total)
    assert "1/1 memories" in output
    assert "k1" in output
    assert "|" in output


def test_format_not_found():
    output = MemoryService.format_not_found("missing-key", "myns")
    assert "not_found" in output
    assert "missing-key" in output


def test_migrate_from_json_via_service(service, tmp_path):
    json_dir = tmp_path / "legacy"
    json_dir.mkdir()
    (json_dir / "note.json").write_text('{"key": "legacy", "content": "migrated"}', encoding="utf-8")

    count = service.migrate_from_json(str(json_dir))

    assert count == 1
    migrated = service.retrieve("legacy", "default")
    assert migrated is not None
    assert migrated.content == "migrated"
