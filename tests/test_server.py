import pytest

import server


def test_remote_homelab_rejects_no_auth(monkeypatch, caplog):
    monkeypatch.setattr(
        server.NVCConfig,
        "from_env",
        classmethod(lambda cls, env_file=None: cls(profile="remote-homelab", transport="sse")),
    )
    monkeypatch.setattr(server.sys, "argv", ["server.py", "--no-auth"])
    caplog.set_level("ERROR")

    with pytest.raises(SystemExit) as exc:
        server.main()

    assert exc.value.code == 1
    assert "--no-auth is not allowed" in caplog.text
