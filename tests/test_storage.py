import sqlite3

import pytest

from core.storage import SQLiteStorage


class TestStoreAndRetrieve:

    def test_store_and_retrieve(self, storage):
        mem = storage.store("k1", "hello world", ["tag1", "tag2"], "Title 1", "ns1")
        assert mem.key == "k1"
        assert mem.content == "hello world"
        assert mem.namespace == "ns1"
        assert mem.title == "Title 1"
        assert mem.tags == ["tag1", "tag2"]
        assert mem.chars == 11
        assert mem.lines == 1

        retrieved = storage.retrieve("k1", "ns1")
        assert retrieved is not None
        assert retrieved.key == "k1"
        assert retrieved.content == "hello world"
        assert retrieved.namespace == "ns1"
        assert retrieved.title == "Title 1"
        assert retrieved.tags == ["tag1", "tag2"]

    def test_retrieve_nonexistent(self, storage):
        assert storage.retrieve("nope") is None


class TestStoreUpdate:

    def test_store_update_creates_version(self, storage):
        storage.store("k1", "v1 content", [], "Title", "default")
        storage.store("k1", "v2 content", [], "Title", "default")

        versions = storage.get_versions("k1")
        assert len(versions) == 1
        assert versions[0].content == "v1 content"
        assert versions[0].version == 1

        retrieved = storage.retrieve("k1")
        assert retrieved.content == "v2 content"


class TestDelete:

    def test_delete(self, storage):
        storage.store("k1", "content", [], "Title", "default")
        assert storage.delete("k1") is True
        assert storage.retrieve("k1") is None

    def test_delete_nonexistent(self, storage):
        assert storage.delete("ghost") is False


class TestListAll:

    def test_list_all(self, storage):
        for i in range(3):
            storage.store(f"k{i}", f"content {i}", [], f"Title {i}", "default")
        result, total = storage.list_all()
        assert len(result) == 3
        assert total == 3

    def test_list_all_by_namespace(self, storage):
        storage.store("k1", "c1", [], "T1", "ns_a")
        storage.store("k2", "c2", [], "T2", "ns_b")
        storage.store("k3", "c3", [], "T3", "ns_a")

        result_a, total_a = storage.list_all(namespace="ns_a")
        assert len(result_a) == 2
        assert total_a == 2
        assert all(m.namespace == "ns_a" for m in result_a)

        result_b, total_b = storage.list_all(namespace="ns_b")
        assert len(result_b) == 1
        assert total_b == 1

    def test_list_all_pagination(self, storage):
        for i in range(5):
            storage.store(f"k{i}", f"content {i}", [], f"Title {i}", "default")
        result, total = storage.list_all(limit=2, offset=0)
        assert len(result) == 2
        assert total == 5
        result2, total2 = storage.list_all(limit=2, offset=3)
        assert len(result2) == 2
        assert total2 == 5


class TestListRecent:

    def test_list_recent(self, storage):
        for i in range(3):
            storage.store(f"k{i}", f"content {i}", [], f"Title {i}", "default")
        result = storage.list_recent(2)
        assert len(result) == 2


class TestSearch:

    def test_search_fts(self, storage):
        storage.store("k1", "the quick brown fox", [], "Fox", "default")
        storage.store("k2", "lazy dog sleeps", [], "Dog", "default")

        results = storage.search("fox")
        assert len(results) >= 1
        assert any(m.key == "k1" for m in results)

    def test_search_empty_query(self, storage):
        storage.store("k1", "content one", [], "T1", "default")
        storage.store("k2", "content two", [], "T2", "default")

        results = storage.search("")
        assert len(results) == 2

    def test_search_no_results(self, storage):
        storage.store("k1", "hello world", [], "T1", "default")
        results = storage.search("zzzznonexistent")
        assert results == []


class TestVersioning:

    def test_get_versions(self, storage):
        storage.store("k1", "v1", [], "T", "default")
        storage.store("k1", "v2", [], "T", "default")
        storage.store("k1", "v3", [], "T", "default")

        versions = storage.get_versions("k1")
        assert len(versions) == 2
        assert versions[0].version == 2
        assert versions[1].version == 1

    def test_restore_version(self, storage):
        storage.store("k1", "original", [], "T", "default")
        storage.store("k1", "updated", [], "T", "default")

        restored = storage.restore_version("k1", "default", 1)
        assert restored is not None
        assert restored.content == "original"

        current = storage.retrieve("k1", "default")
        assert current.content == "original"

    def test_restore_nonexistent_version(self, storage):
        assert storage.restore_version("nope", "default", 99) is None


class TestValidation:

    def test_validation_empty_key(self, storage):
        with pytest.raises(ValueError, match="Key cannot be empty"):
            storage.store("", "content", [], "T", "default")

    def test_validation_key_too_long(self, storage):
        with pytest.raises(ValueError, match="Key too long"):
            storage.store("k" * 300, "content", [], "T", "default")

    def test_validation_content_too_long(self, storage):
        with pytest.raises(ValueError, match="Content too long"):
            storage.store("k1", "x" * 1_000_001, [], "T", "default")


class TestStatsAndNamespaces:

    def test_get_stats(self, storage):
        storage.store("k1", "hello", [], "T1", "default")
        storage.store("k2", "world!", [], "T2", "ns2")

        stats = storage.get_stats()
        assert stats.total_memories == 2
        assert stats.total_chars == 11
        assert stats.namespaces == 2
        assert stats.db_size_kb > 0

    def test_list_namespaces(self, storage):
        storage.store("k1", "c1", [], "T1", "alpha")
        storage.store("k2", "c2", [], "T2", "beta")
        storage.store("k3", "c3", [], "T3", "alpha")

        ns = storage.list_namespaces()
        assert ns == ["alpha", "beta"]


class TestTagsAndSchema:

    def test_tags_round_trip(self, storage):
        storage.store("k1", "content", ["python", "testing", "ci"], "T1", "default")
        retrieved = storage.retrieve("k1")
        assert retrieved.tags == ["python", "testing", "ci"]

    def test_embedding_column_exists(self, storage):
        row = storage._conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='memories'"
        ).fetchone()
        assert "embedding" in row[0].lower()


class TestLifecycle:

    def test_close_closes_connection(self, storage):
        storage.close()
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            storage.retrieve("k1")

    def test_context_manager_closes_connection(self, config):
        with SQLiteStorage(config) as storage:
            storage.store("k1", "content", [], "Title", "default")

        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            storage.retrieve("k1")

    def test_backup_and_restore_round_trip(self, storage, tmp_path):
        storage.store("k1", "original", [], "Title", "default")
        backup_path = tmp_path / "backup.db"

        storage.backup_to(backup_path)
        storage.store("k1", "updated", [], "Title", "default")
        storage.restore_from(backup_path)

        restored = storage.retrieve("k1", "default")
        assert restored is not None
        assert restored.content == "original"
