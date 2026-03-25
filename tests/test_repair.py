from core.repair import run_repair


def test_run_repair_smoke(storage):
    storage.store("k1", "content", [], "Title", "default")

    results = run_repair(storage)

    assert results
    assert any(status in {"OK", "SKIP", "WARN"} for status, _ in results)
