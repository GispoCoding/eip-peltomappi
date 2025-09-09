from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
from uuid import UUID


from peltomappi.composition import Composition
from test.utils.classes import ContainedComposition, CompositionBackendTest


def test_add_subproject_from_parcelspec():
    # FIXME: implement
    pass


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

    os.chdir(comp_dir)

    comp = Composition.from_json(composition_path, test_backend)

    assert comp.id() == UUID("31668d9c-3d85-49c2-a4f9-534a9238ff2f")
    assert comp.name() == "saved_composition"
    assert comp.mergin_workspace() == "test_workspace"
    assert comp.mergin_server() == "test_server"
    assert comp.template_name() == "template"

    # absolute paths are used when writing a subproject/composition json but
    # those are difficult in tests so the testdata jsons use relative paths

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
