import logging
import shutil
import tempfile
import pytest

from pathlib import Path

from peltomappi.composition import Composition
from peltomappi.logger import LOGGER
from test.utils.classes import ContainedComposition, CompositionBackendTest
from test.utils.utils import testdata_path

LOGGER.setLevel(logging.CRITICAL)


@pytest.fixture
def test_template_project() -> Path:
    return testdata_path() / "test_saved_composition/template"


@pytest.fixture
def test_full_data() -> Path:
    return testdata_path() / "test_full_data"


@pytest.fixture
def subproject_json_1() -> Path:
    return testdata_path() / "test_subproject_1.json"


@pytest.fixture
def subproject_json_2() -> Path:
    return testdata_path() / "test_subproject_2.json"


@pytest.fixture
def subproject_with_data_folder() -> Path:
    return testdata_path() / "test_subproject_with_data"


@pytest.fixture
def parcel_spec() -> Path:
    return testdata_path() / "test_parcelspec.json"


@pytest.fixture
def composition_parcelspec_json_1() -> Path:
    return testdata_path() / "test_composition_parcelspec_1.json"


@pytest.fixture
def composition_parcelspec_json_2() -> Path:
    return testdata_path() / "test_composition_parcelspec_2.json"


@pytest.fixture
def composition_parcelspec_json_3() -> Path:
    return testdata_path() / "test_composition_parcelspec_3.json"


@pytest.fixture
def test_backend() -> CompositionBackendTest:
    return CompositionBackendTest(testdata_path() / "testbackend")


@pytest.fixture
def saved_composition() -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory()
    shutil.copytree(testdata_path() / "test_saved_composition", Path(temp_dir.name) / "test_saved_composition")

    return temp_dir


@pytest.fixture
def initialized_composition(
    test_backend: CompositionBackendTest,
    composition_parcelspec_json_1: Path,
    composition_parcelspec_json_2: Path,
    composition_parcelspec_json_3: Path,
    test_full_data: Path,
) -> ContainedComposition:
    temp_dir = tempfile.TemporaryDirectory()
    comp_path = Path(temp_dir.name) / "composition"
    comp = Composition.initialize(
        comp_path,
        "template",
        "initialized_composition",
        "test_workspace",
        "mock_server",
        test_backend,
    )

    for file in test_full_data.iterdir():
        shutil.copy(file, comp.full_data_path())

    comp.add_subproject_from_parcelspec(composition_parcelspec_json_1)
    comp.add_subproject_from_parcelspec(composition_parcelspec_json_2)
    comp.add_subproject_from_parcelspec(composition_parcelspec_json_3)

    return ContainedComposition(temp_dir=temp_dir, composition=comp)
