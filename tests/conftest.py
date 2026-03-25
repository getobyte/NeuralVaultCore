import pytest

from core.config import NVCConfig
from core.storage import SQLiteStorage


@pytest.fixture
def config(tmp_path):
    return NVCConfig(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def storage(config):
    s = SQLiteStorage(config)
    yield s
    s.close()
