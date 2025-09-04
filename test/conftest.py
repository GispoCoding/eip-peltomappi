import logging
import tempfile
import pytest

from pathlib import Path

from peltomappi.composition import Composition
from peltomappi.logger import LOGGER
from test.utils.classes import ContainedComposition

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


@pytest.fixture
def contained_composition(
    composition_subproject_json_1: Path,
    composition_subproject_json_2: Path,
    composition_subproject_json_3: Path,
    test_template_project: Path,
    test_full_data: Path,
) -> ContainedComposition:
    temp_dir = tempfile.TemporaryDirectory()
    return ContainedComposition(
        temp_dir=temp_dir,
        composition=Composition.from_empty_subprojects(
            [
                composition_subproject_json_1,
                composition_subproject_json_2,
                composition_subproject_json_3,
            ],
            test_template_project,
            test_full_data,
            Path(temp_dir.name) / "output",
            "test_workspace",
            "test_composition",
            "test_server",
        ),
    )
