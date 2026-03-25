from core.watcher import FileChangeHandler


class DummyStorage:
    def __init__(self):
        self.calls = []

    def store(self, key, content, tags, title, namespace):
        self.calls.append({
            "key": key,
            "content": content,
            "tags": tags,
            "title": title,
            "namespace": namespace,
        })


def test_file_change_handler_flushes_summary():
    storage = DummyStorage()
    handler = FileChangeHandler(storage, "watch:repo", debounce=0.0)

    handler.on_change("modified", "/tmp/app.py")

    assert len(storage.calls) == 1
    assert "modified: 1 file(s)" in storage.calls[0]["content"]
    assert storage.calls[0]["namespace"] == "watch:repo"


def test_file_change_handler_ignores_noise():
    storage = DummyStorage()
    handler = FileChangeHandler(storage, "watch:repo", debounce=0.0)

    handler.on_change("modified", "/tmp/node_modules/react/index.js")
    handler.on_change("modified", "/tmp/cache.pyc")

    assert storage.calls == []
