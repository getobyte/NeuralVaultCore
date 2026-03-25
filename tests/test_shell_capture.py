import pytest
from core.shell_capture import _should_capture, _dedup_key
import core.shell_capture as shell_capture


def test_should_capture_normal_command():
    assert _should_capture("docker compose up -d") is True

def test_should_capture_ignores_cd():
    assert _should_capture("cd /home") is False

def test_should_capture_ignores_ls():
    assert _should_capture("ls -la") is False

def test_should_capture_ignores_short():
    assert _should_capture("pwd") is False
    assert _should_capture("git") is False

def test_should_capture_ignores_clear():
    assert _should_capture("clear") is False

def test_dedup_key_consistent():
    k1 = _dedup_key("docker compose up", "myhost")
    k2 = _dedup_key("docker compose up", "myhost")
    assert k1 == k2
    assert k1.startswith("shell:myhost:")

def test_dedup_key_different_commands():
    k1 = _dedup_key("docker compose up", "myhost")
    k2 = _dedup_key("docker compose down", "myhost")
    assert k1 != k2


def test_capture_command_closes_storage(monkeypatch):
    events = []

    class DummyStorage:
        def __init__(self, config):
            events.append("init")

        def __enter__(self):
            events.append("enter")
            return self

        def __exit__(self, exc_type, exc, tb):
            events.append("exit")

        def retrieve(self, key, namespace="default"):
            return None

        def store(self, key, content, tags, title, namespace):
            events.append(("store", key, namespace))

    monkeypatch.setattr("core.storage.SQLiteStorage", DummyStorage)

    assert shell_capture.capture_command("docker compose up -d") is True
    assert events[:2] == ["init", "enter"]
    assert events[-1] == "exit"
    assert any(isinstance(event, tuple) and event[0] == "store" for event in events)
