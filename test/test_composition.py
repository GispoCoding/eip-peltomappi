from pathlib import Path
from uuid import UUID

import pytest

from peltomappi.composition import CompositionError
from test.utils.classes import ContainedComposition


def test_from_empty_subprojects(
    test_template_project: Path,
    contained_composition: ContainedComposition,
):
    composition = contained_composition.composition
    temp_path = Path(contained_composition.temp_dir.name)

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
    assert subproject_1.path() == (temp_path / "output" / "test_composition_subproject_1")
    assert subproject_1.modified() == []
    assert subproject_1.composition_id() == composition.id()

    assert subproject_2.name() == "test_composition_subproject_2"
    assert subproject_2.path() == (temp_path / "output" / "test_composition_subproject_2")
    assert subproject_2.modified() == []
    assert subproject_2.composition_id() == composition.id()

    assert subproject_3.name() == "test_composition_subproject_3"
    assert subproject_3.path() == (temp_path / "output" / "test_composition_subproject_3")
    assert subproject_3.modified() == []
    assert subproject_3.composition_id() == composition.id()


def test_to_json_dict(
    contained_composition: ContainedComposition,
    test_template_project: Path,
):
    composition = contained_composition.composition
    output_path = Path(contained_composition.temp_dir.name) / "output"

    d = composition.to_json_dict()

    try:
        UUID(d["compositionId"], version=4)
    except:  # noqa: E722
        assert False

    assert d["compositionName"] == "test_composition"
    assert d["merginWorkspace"] == "test_workspace"
    assert d["merginServer"] == "test_server"
    assert d["templateProjectPath"] == test_template_project.name

    assert d["subprojects"] == [
        f"{output_path}/test_composition_subproject_1",
        f"{output_path}/test_composition_subproject_2",
        f"{output_path}/test_composition_subproject_3",
    ]


def test_save(contained_composition: ContainedComposition):
    composition = contained_composition.composition

    with pytest.raises(CompositionError):
        composition.save()

    path = Path(contained_composition.temp_dir.name) / "composition.json"

    composition.set_path(path)
    composition.save()

    expected = f"""{{
    "compositionId": "{composition.id()}",
    "compositionName": "test_composition",
    "merginWorkspace": "test_workspace",
    "merginServer": "test_server",
    "templateProjectPath": "test_template_project",
    "subprojects": [
        "/tmp/{path.parent.stem}/output/test_composition_subproject_1",
        "/tmp/{path.parent.stem}/output/test_composition_subproject_2",
        "/tmp/{path.parent.stem}/output/test_composition_subproject_3"
    ]
}}"""

    assert path.read_text() == expected
