from core.config import NVCConfig
from core.doctor import run_doctor


def test_doctor_basic(tmp_path):
    config = NVCConfig(db_path=str(tmp_path / "test.db"))
    results = run_doctor(config)
    assert len(results) > 0
    assert any(s == "OK" and "Python" in m for s, _, m in results)


def test_doctor_missing_db(tmp_path):
    config = NVCConfig(db_path=str(tmp_path / "nonexistent" / "test.db"))
    results = run_doctor(config)
    assert any(s == "ERROR" and "parent dir" in m for s, _, m in results)


def test_doctor_closes_socket_on_bind_error(tmp_path, monkeypatch):
    closed = []

    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            closed.append(True)

        def settimeout(self, value):
            return None

        def bind(self, address):
            raise OSError("in use")

    monkeypatch.setattr("core.doctor.socket.socket", lambda *args, **kwargs: FakeSocket())

    config = NVCConfig(db_path=str(tmp_path / "test.db"))
    results = run_doctor(config)

    assert closed
    assert any(status == "WARN" and category == "ports" for status, category, _ in results)
