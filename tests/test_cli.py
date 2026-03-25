import argparse

import pytest

import nvc
from core.config import NVCConfig
from core.storage import SQLiteStorage


@pytest.fixture
def cli_storage(tmp_path):
    old_storage = nvc._storage
    storage = SQLiteStorage(NVCConfig(db_path=str(tmp_path / "cli.db")))
    nvc._storage = storage
    try:
        yield storage
    finally:
        if nvc._storage is storage:
            nvc._storage = None
        storage.close()
        nvc._storage = old_storage


def test_get_parser_accepts_namespace():
    args = nvc.build_parser().parse_args(["get", "shared-key", "--ns", "project:alpha"])
    assert args.ns == "project:alpha"


def test_cmd_get_uses_namespace(cli_storage, capsys):
    cli_storage.store("shared-key", "default content", [], "Default", "default")
    cli_storage.store("shared-key", "project content", [], "Project", "project:alpha")

    nvc.cmd_get(argparse.Namespace(key="shared-key", ns="project:alpha"))

    out = capsys.readouterr().out
    assert "project content" in out
    assert "project:alpha" in out


def test_cmd_restore_rejects_non_positive_version(capsys):
    with pytest.raises(SystemExit) as exc:
        nvc.cmd_restore(argparse.Namespace(key="shared-key", version=0, yes=True))

    assert exc.value.code == 1
    assert "Version must be >= 1" in capsys.readouterr().err
