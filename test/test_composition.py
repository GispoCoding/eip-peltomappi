from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from uuid import UUID

import pytest

from peltomappi.composition import Composition, CompositionError
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

    assert subproject_1.name() == "test_composition_parcelspec_1"
    assert subproject_1.path() == (temp_path / "output" / "test_composition_parcelspec_1")
    assert subproject_1.modified() == []
    assert subproject_1.composition_id() == composition.id()

    assert subproject_2.name() == "test_composition_parcelspec_2"
    assert subproject_2.path() == (temp_path / "output" / "test_composition_parcelspec_2")
    assert subproject_2.modified() == []
    assert subproject_2.composition_id() == composition.id()

    assert subproject_3.name() == "test_composition_parcelspec_3"
    assert subproject_3.path() == (temp_path / "output" / "test_composition_parcelspec_3")
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
    assert d["templateProjectPath"] == test_template_project.__str__()

    assert d["subprojects"] == [
        f"{output_path}/test_composition_parcelspec_1/peltomappi_subproject.json",
        f"{output_path}/test_composition_parcelspec_2/peltomappi_subproject.json",
        f"{output_path}/test_composition_parcelspec_3/peltomappi_subproject.json",
    ]


def test_save(
    test_template_project: Path,
    contained_composition: ContainedComposition,
):
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
    "templateProjectPath": "{test_template_project}",
    "subprojects": [
        "/tmp/{path.parent.stem}/output/test_composition_parcelspec_1/peltomappi_subproject.json",
        "/tmp/{path.parent.stem}/output/test_composition_parcelspec_2/peltomappi_subproject.json",
        "/tmp/{path.parent.stem}/output/test_composition_parcelspec_3/peltomappi_subproject.json"
    ]
}}"""

    assert path.read_text() == expected


def test_from_json(saved_composition: tempfile.TemporaryDirectory):
    comp_dir = Path(saved_composition.name) / "test_saved_composition"
    composition_path = comp_dir / "composition.json"

    os.chdir(comp_dir)

    comp = Composition.from_json(composition_path)

    assert comp.id() == UUID("31668d9c-3d85-49c2-a4f9-534a9238ff2f")
    assert comp.name() == "saved_composition"
    assert comp.mergin_workspace() == "test_workspace"
    assert comp.mergin_server() == "test_server"
    assert comp.template_project_path() == Path("/somewhere")

    # absolute paths are used when writing a subproject/composition json but
    # those are difficult in tests so the testdata jsons use relative paths

    subprojects = comp.subprojects()
    assert len(subprojects) == 2

    assert subprojects[0].id() == UUID("196d686e-885f-4514-8de6-8aec3902b97a")
    assert subprojects[0].name() == "saved_subproject_1"
    assert subprojects[0].path() == Path("/somewhere")
    assert subprojects[0].field_parcel_ids() == ["1111111111", "2222222222"]
    assert subprojects[0].created() == datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert subprojects[0].composition_id() == comp.id()

    assert subprojects[1].id() == UUID("402f32a5-929d-49d8-8793-bb73d3830da9")
    assert subprojects[1].name() == "saved_subproject_2"
    assert subprojects[1].path() == Path("/somewhere/else")
    assert subprojects[1].field_parcel_ids() == ["2222222222"]
    assert subprojects[1].created() == datetime(1970, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert subprojects[1].composition_id() == comp.id()
