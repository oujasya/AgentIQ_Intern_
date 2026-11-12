import pytest

from agentiq.api import create_app
from agentiq.data import ingest, sample_records
from agentiq.settings import Settings
from agentiq.storage import Store


@pytest.fixture
def clean_records():
    return ingest(sample_records())["records"]


@pytest.fixture
def valid_record(clean_records):
    return clean_records[0].copy()


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "test.sqlite3")


@pytest.fixture
def app(tmp_path):
    return create_app(Settings(database_path=str(tmp_path / "api.sqlite3")))
