from pathlib import Path
from uuid import UUID

from peltomappi.composition import Composition

import tempfile


def test_from_empty_subprojects(
    composition_subproject_json_1: Path,
    composition_subproject_json_2: Path,
    composition_subproject_json_3: Path,
    test_template_project: Path,
    test_full_data: Path,
):
    tempdir = tempfile.TemporaryDirectory()
    temp_path = Path(tempdir.name) / "subprojects"

    composition = Composition.from_empty_subprojects(
        [
            composition_subproject_json_1,
            composition_subproject_json_2,
            composition_subproject_json_3,
        ],
        test_template_project,
        test_full_data,
        temp_path,
        "test_workspace",
        "test_composition",
        "test_server",
    )

    assert isinstance(composition.id(), UUID)
    assert composition.name() == "test_composition"
    assert composition.mergin_workspace() == "test_workspace"
    assert composition.mergin_server() == "test_server"
    assert composition.template_project_path() == test_template_project

    assert len(composition.subprojects()) == 3

    subproject_1 = composition.subprojects()[0]
    subproject_2 = composition.subprojects()[1]
    subproject_3 = composition.subprojects()[2]

    assert subproject_1.name() == "test_composition_subproject_1"
    assert subproject_1.path() == (temp_path / "test_composition_subproject_1")
    assert subproject_1.modified() == []
    assert subproject_1.composition_id() == composition.id()

    assert subproject_2.name() == "test_composition_subproject_2"
    assert subproject_2.path() == (temp_path / "test_composition_subproject_2")
    assert subproject_2.modified() == []
    assert subproject_2.composition_id() == composition.id()

    assert subproject_3.name() == "test_composition_subproject_3"
    assert subproject_3.path() == (temp_path / "test_composition_subproject_3")
    assert subproject_3.modified() == []
    assert subproject_3.composition_id() == composition.id()
