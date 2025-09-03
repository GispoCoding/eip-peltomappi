import logging
import pytest

from pathlib import Path

from peltomappi.logger import LOGGER

LOGGER.setLevel(logging.CRITICAL)


def _testdata_path() -> Path:
    return Path(__file__).resolve().parent / "testdata"


@pytest.fixture
def test_template_project() -> Path:
    return _testdata_path() / "test_template_project"


@pytest.fixture
def test_full_data() -> Path:
    return _testdata_path() / "test_full_data"


@pytest.fixture
def subproject_json_1() -> Path:
    return _testdata_path() / "test_subproject_1.json"


@pytest.fixture
def subproject_json_2() -> Path:
    return _testdata_path() / "test_subproject_2.json"


@pytest.fixture
def subproject_json_3() -> Path:
    return _testdata_path() / "test_subproject_3.json"


@pytest.fixture
def composition_subproject_json_1() -> Path:
    return _testdata_path() / "test_composition_subproject_1.json"


@pytest.fixture
def composition_subproject_json_2() -> Path:
    return _testdata_path() / "test_composition_subproject_2.json"


@pytest.fixture
def composition_subproject_json_3() -> Path:
    return _testdata_path() / "test_composition_subproject_3.json"
