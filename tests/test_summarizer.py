from core.models import Memory
from core.summarizer import summarize_heuristic


def _make_memory(key, content, namespace, tags=None, updated_at="2026-03-24T12:00:00+00:00"):
    return Memory(
        key=key, content=content, namespace=namespace,
        title=key, tags=tags or [], updated_at=updated_at,
    )


def test_summarize_empty():
    result = summarize_heuristic([])
    assert "No events" in result


def test_summarize_shell_events():
    mems = [
        _make_memory("s1", "docker compose up", "shell:host", ["shell"]),
        _make_memory("s2", "docker compose down", "shell:host", ["shell"]),
        _make_memory("s3", "python server.py", "shell:host", ["shell"]),
    ]
    result = summarize_heuristic(mems)
    assert "3 commands" in result or "3 events" in result
    assert "shell:host" in result


def test_summarize_git_events():
    mems = [
        _make_memory("g1", "Commit: abc\nBranch: main", "git:myrepo", ["git", "commit"]),
        _make_memory("g2", "Merge: def\nBranch: main", "git:myrepo", ["git", "merge"]),
    ]
    result = summarize_heuristic(mems)
    assert "git:myrepo" in result
