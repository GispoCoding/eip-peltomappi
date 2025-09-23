from datetime import datetime, timezone
import shutil
from pathlib import Path
import tempfile
from uuid import UUID

from freezegun import freeze_time

import pytest

from peltomappi.composition import Composition, CompositionError
from peltomappi.subproject import TEMPLATE_MERGIN_CONFIG_NAME, TEMPLATE_QGIS_PROJECT_NAME, ModificationType
from test.utils.classes import ContainedComposition, CompositionBackendTest


def test_initialize(test_backend: CompositionBackendTest):
    temp_dir = tempfile.TemporaryDirectory()
    comp_path = Path(temp_dir.name) / "composition"
    Composition.initialize(
        comp_path,
        "template",
        "test_comp",
        "test_workspace",
        "mock_server",
        test_backend,
    )

    assert (comp_path / "template").exists()
    assert (comp_path / "template/peltolohkot_2023.gpkg").exists()
    assert (comp_path / "template/peltolohkot_2024.gpkg").exists()
    assert (comp_path / "template/peltomappi.qgs").exists()
    assert (comp_path / ".composition/full_data").exists()
    assert (comp_path / ".composition/composition.json").exists()


def test_add_subproject_from_parcelspec(
    test_backend: CompositionBackendTest, composition_parcelspec_json_1: Path, test_full_data: Path
):
    temp_dir = tempfile.TemporaryDirectory()
    comp_path = Path(temp_dir.name) / "composition"
    comp = Composition.initialize(
        comp_path,
        "template",
        "test_comp",
        "test_workspace",
        "mock_server",
        test_backend,
    )

    for file in test_full_data.iterdir():
        shutil.copy(file, comp.full_data_path())

    comp.add_subproject_from_parcelspec(composition_parcelspec_json_1)

    subprojects = comp.subprojects()
    assert len(subprojects) == 1

    sp = subprojects[0]
    assert sp.name() == "test_composition_parcelspec_1"
    assert sp.field_parcel_ids() == ["3333333333"]


def test_to_json_dict(initialized_composition: ContainedComposition):
    composition = initialized_composition.composition
    d = composition.to_json_dict()

    try:
        UUID(d["compositionId"], version=4)
    except:  # noqa: E722
        assert False

    assert d["compositionName"] == "initialized_composition"
    assert d["merginWorkspace"] == "test_workspace"
    assert d["merginServer"] == "mock_server"
    assert d["templateName"] == "template"

    assert d["subprojects"] == [
        "test_composition_parcelspec_1",
        "test_composition_parcelspec_2",
        "test_composition_parcelspec_3",
    ]


def test_save(
    initialized_composition: ContainedComposition,
):
    composition = initialized_composition.composition
    composition.save()

    expected = f"""{{
    "compositionId": "{composition.id()}",
    "compositionName": "initialized_composition",
    "merginWorkspace": "test_workspace",
    "merginServer": "mock_server",
    "templateName": "template",
    "subprojects": [
        "test_composition_parcelspec_1",
        "test_composition_parcelspec_2",
        "test_composition_parcelspec_3"
    ]
}}"""

    assert composition.json_config_path().read_text() == expected


def test_from_json(
    saved_composition: tempfile.TemporaryDirectory,
    test_backend: CompositionBackendTest,
):
    comp_dir = Path(saved_composition.name) / "test_saved_composition"
    composition_path = comp_dir / ".composition/composition.json"

    comp = Composition.from_json(composition_path, test_backend)

    assert comp.id() == UUID("31668d9c-3d85-49c2-a4f9-534a9238ff2f")
    assert comp.name() == "saved_composition"
    assert comp.mergin_workspace() == "test_workspace"
    assert comp.mergin_server() == "test_server"
    assert comp.template_name() == "template"

    subprojects = comp.subprojects()
    assert len(subprojects) == 2

    assert subprojects[0].id() == UUID("196d686e-885f-4514-8de6-8aec3902b97a")
    assert subprojects[0].name() == "saved_subproject_1"
    assert subprojects[0].field_parcel_ids() == ["1111111111", "2222222222"]
    assert subprojects[0].created() == datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert subprojects[0].composition_id() == comp.id()

    assert subprojects[1].id() == UUID("402f32a5-929d-49d8-8793-bb73d3830da9")
    assert subprojects[1].name() == "saved_subproject_2"
    assert subprojects[1].field_parcel_ids() == ["2222222222"]
    assert subprojects[1].created() == datetime(1970, 5, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert subprojects[1].composition_id() == comp.id()


def test_path_getters(
    saved_composition: tempfile.TemporaryDirectory,
    test_backend: CompositionBackendTest,
):
    comp_dir = (Path(saved_composition.name) / "test_saved_composition").resolve()
    composition_path = (comp_dir / ".composition/composition.json").resolve()

    comp = Composition.from_json(composition_path, test_backend)

    assert comp.projects_path() == comp_dir
    assert comp.template_project_path() == comp_dir / "template"
    assert comp.full_data_path() == comp_dir / ".composition/full_data"
    assert comp.subproject_path("subproject_1") == comp_dir / "subproject_1"
    assert comp.json_config_path() == comp_dir / ".composition/composition.json"


def test_name_getters(
    saved_composition: tempfile.TemporaryDirectory,
    test_backend: CompositionBackendTest,
):
    comp_dir = Path(saved_composition.name) / "test_saved_composition"
    composition_path = comp_dir / ".composition/composition.json"

    comp = Composition.from_json(composition_path, test_backend)

    assert comp.mergin_name() == "saved_composition"
    assert comp.mergin_name_with_workspace() == "test_workspace/saved_composition"
    assert comp.subproject_mergin_name("subproject_1") == "saved_composition_subproject_1"
    assert comp.subproject_mergin_name_with_workspace("subproject_1") == "test_workspace/saved_composition_subproject_1"
    assert comp.template_mergin_name_with_workspace() == "test_workspace/template"


@freeze_time("1970-01-01 00:00:00")
def test_subprojects_match_template(
    saved_composition: tempfile.TemporaryDirectory,
    test_backend: CompositionBackendTest,
):
    comp_dir = Path(saved_composition.name) / "test_saved_composition"
    composition_path = comp_dir / ".composition/composition.json"

    comp = Composition.from_json(composition_path, test_backend)

    with pytest.raises(CompositionError):
        comp.subprojects_match_template()

    with open(comp.template_project_path() / TEMPLATE_QGIS_PROJECT_NAME, "w") as file:
        file.write("test_modification")

    with open(comp.template_project_path() / TEMPLATE_MERGIN_CONFIG_NAME, "w") as file:
        file.write("test mod")

    comp.subprojects_match_template()

    sp_1 = comp.subprojects()[0]
    sp_2 = comp.subprojects()[1]

    assert (sp_1.path() / TEMPLATE_QGIS_PROJECT_NAME).read_text() == "test_modification"
    assert (sp_1.path() / TEMPLATE_MERGIN_CONFIG_NAME).read_text() == "test mod"
    assert (sp_2.path() / TEMPLATE_QGIS_PROJECT_NAME).read_text() == "test_modification"
    assert (sp_2.path() / TEMPLATE_MERGIN_CONFIG_NAME).read_text() == "test mod"

    assert len(sp_1.modified()) == 1
    assert len(sp_2.modified()) == 1

    assert sp_1.modified()[0].timestamp == datetime.fromtimestamp(0)
    assert sp_2.modified()[0].timestamp == datetime.fromtimestamp(0)

    assert sp_1.modified()[0].mod_type == ModificationType.PROJECT_UPDATE
    assert sp_2.modified()[0].mod_type == ModificationType.PROJECT_UPDATE
