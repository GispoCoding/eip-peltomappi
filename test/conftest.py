import logging
import pytest

from pathlib import Path

from peltomappi.logger import LOGGER

LOGGER.setLevel(logging.CRITICAL)


def _testdata_path() -> Path:
    return Path(__file__).resolve().parent / "testdata"


def _expected_path() -> Path:
    return _testdata_path() / "expected"


@pytest.fixture
def field_parcel_mock_uri() -> Path:
    return _testdata_path() / "field_parcel_mock_ds.gpkg"


@pytest.fixture
def fulldata() -> Path:
    return _testdata_path() / "fulldata.gpkg"


@pytest.fixture
def field_parcel_config() -> Path:
    return _testdata_path() / "field_parcel_config.gpkg"


@pytest.fixture
def dummy_project() -> Path:
    return _testdata_path() / "dummy_project"


@pytest.fixture
def dummy_project_full_data() -> Path:
    return _testdata_path() / "dummy_project_full_data"


@pytest.fixture
def config_json() -> Path:
    return _testdata_path() / "config.json"


@pytest.fixture
def config_gpkg() -> Path:
    return _expected_path() / "config_gpkg.gpkg"
