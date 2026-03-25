import core.config
import core.daemon as daemon


def test_run_daemon_logs_invalid_config(monkeypatch, caplog):
    monkeypatch.setattr(
        core.config.NVCConfig,
        "from_env",
        classmethod(lambda cls, env_file=None: (_ for _ in ()).throw(ValueError("bad env"))),
    )
    caplog.set_level("ERROR")

    daemon._run_daemon([], 1.0)

    assert "Failed to load daemon config" in caplog.text
