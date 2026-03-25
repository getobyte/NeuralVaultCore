from core.models import Memory, StorageStats, Version


def test_memory_post_init_defaults():
    mem = Memory(key="mykey", content="line1\nline2\nline3")
    assert mem.title == "mykey"
    assert mem.chars == 17
    assert mem.lines == 3


def test_memory_from_row():
    row = {
        "key": "k1",
        "content": "hello",
        "namespace": "ns1",
        "title": "My Title",
        "tags": "a,b,c",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-02T00:00:00",
        "chars": 5,
        "lines": 1,
    }
    mem = Memory.from_row(row)
    assert mem.key == "k1"
    assert mem.content == "hello"
    assert mem.namespace == "ns1"
    assert mem.title == "My Title"
    assert mem.tags == ["a", "b", "c"]
    assert mem.created_at == "2025-01-01T00:00:00"
    assert mem.updated_at == "2025-01-02T00:00:00"
    assert mem.chars == 5
    assert mem.lines == 1


def test_memory_tags_str():
    mem = Memory(key="k", content="c", tags=["x", "y", "z"])
    assert mem.tags_str == "x,y,z"


def test_memory_tags_str_empty():
    mem = Memory(key="k", content="c", tags=[])
    assert mem.tags_str == ""


def test_version_from_row():
    row = {
        "key": "k1",
        "version": 3,
        "title": "T",
        "content": "old content",
        "tags": "t1,t2",
        "namespace": "ns",
        "saved_at": "2025-06-01T12:00:00",
    }
    ver = Version.from_row(row)
    assert ver.key == "k1"
    assert ver.version == 3
    assert ver.title == "T"
    assert ver.content == "old content"
    assert ver.tags == ["t1", "t2"]
    assert ver.namespace == "ns"
    assert ver.saved_at == "2025-06-01T12:00:00"


def test_version_tags_str():
    ver = Version(key="k", version=1, title="T", content="c", tags=["a", "b"])
    assert ver.tags_str == "a,b"


def test_version_tags_str_empty():
    ver = Version(key="k", version=1, title="T", content="c", tags=[])
    assert ver.tags_str == ""


def test_storage_stats_defaults():
    stats = StorageStats()
    assert stats.total_memories == 0
    assert stats.total_chars == 0
    assert stats.namespaces == 0
    assert stats.db_size_kb == 0.0
    assert stats.db_path == ""
