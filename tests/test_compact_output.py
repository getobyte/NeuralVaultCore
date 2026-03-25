"""Verify MCP outputs are compact (no emoji, pipe-delimited, within token budget)."""

from core.config import NVCConfig
from core.storage import SQLiteStorage
from core.service import MemoryService


def _make_service(tmp_path):
    config = NVCConfig(db_path=str(tmp_path / "test.db"))
    storage = SQLiteStorage(config)
    return MemoryService(storage)


def test_format_compact_no_emoji(tmp_path):
    svc = _make_service(tmp_path)
    svc.store("k1", "hello world", ["tag1"], "My Title", "default")
    memories, total = svc.list_memories()
    output = MemoryService.format_compact_list(memories, total)
    # No emoji
    for char in output:
        assert ord(char) < 0x1F600 or ord(char) > 0x1F64F, f"Emoji found: {char}"
    # Pipe delimited
    assert "|" in output


def test_not_found_is_actionable(tmp_path):
    output = MemoryService.format_not_found("missing", "default")
    assert "not_found" in output
    assert "search_memories" in output or "list_all" in output


def test_compact_list_token_budget(tmp_path):
    svc = _make_service(tmp_path)
    # Store 20 memories
    for i in range(20):
        svc.store(f"key-{i}", f"Content for memory {i} " * 10, [f"tag{i}"], f"Title {i}", "default")
    memories, total = svc.list_memories(limit=20)
    output = MemoryService.format_compact_list(memories, total)
    # 20 memories should fit in ~2000 chars
    assert len(output) < 3000, f"Output too large: {len(output)} chars"
    estimated_tokens = len(output) // 4
    assert estimated_tokens < 750, f"Too many tokens: {estimated_tokens}"
