import pytest

from pathlib import Path


def _testdata_path() -> Path:
    return Path(__file__).resolve().parent / "testdata"


@pytest.fixture
def field_parcel_mock_uri() -> Path:
    return _testdata_path() / "field_parcel_mock_ds.gpkg"


@pytest.fixture
def field_parcel_config() -> Path:
    return _testdata_path() / "field_parcel_config.gpkg"
