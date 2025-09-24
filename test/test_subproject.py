from datetime import datetime, timezone
from pathlib import Path
import shutil
from uuid import UUID


from peltomappi.subproject import (
    ModificationAction,
    ModificationType,
    Subproject,
)


import tempfile


def test_from_json(
    subproject_json_1: Path,
    subproject_json_2: Path,
):
    subproject_1 = Subproject.from_json(subproject_json_1)
    assert subproject_1.id() == UUID("30bf748e-6dab-4dcd-95ea-9903c6524150")
    assert subproject_1.name() == "test_subproject_2"
    assert subproject_1.field_parcel_ids() == ["1111111111", "2222222222"]
    assert subproject_1.created() == datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert subproject_1.modified() == []
    assert subproject_1.composition_id() == UUID("234634d0-7b02-4634-b520-1dc0331dd2bc")

    subproject_2 = Subproject.from_json(subproject_json_2)
    assert subproject_2.id() == UUID("0069d09b-890a-4d1a-8922-d3b0fc8342b1")
    assert subproject_2.name() == "test_subproject_3"
    assert subproject_2.field_parcel_ids() == ["1111111111"]
    assert subproject_2.created() == datetime(1971, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert subproject_2.modified() == [
        ModificationAction(
            mod_type=ModificationType.PROJECT_UPDATE, timestamp=datetime(1971, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        ),
        ModificationAction(
            mod_type=ModificationType.WEATHER_UPDATE, timestamp=datetime(1971, 1, 3, 0, 0, 0, tzinfo=timezone.utc)
        ),
    ]
    assert subproject_2.composition_id() == UUID("aecea423-a08a-4a33-8a11-18dfb13f171c")


def test_to_json_dict(
    subproject_json_1: Path,
    subproject_json_2: Path,
):
    subproject_1 = Subproject.from_json(subproject_json_1)
    dict_1 = subproject_1.to_json_dict()
    assert dict_1["id"] == "30bf748e-6dab-4dcd-95ea-9903c6524150"
    assert dict_1["name"] == "test_subproject_2"
    assert dict_1["created"] == datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()
    assert dict_1["fieldParcelIds"] == ["1111111111", "2222222222"]
    assert dict_1.get("modified") is None
    assert dict_1["compositionId"] == "234634d0-7b02-4634-b520-1dc0331dd2bc"

    subproject_2 = Subproject.from_json(subproject_json_2)
    dict_2 = subproject_2.to_json_dict()
    assert dict_2["id"] == "0069d09b-890a-4d1a-8922-d3b0fc8342b1"
    assert dict_2["name"] == "test_subproject_3"
    assert dict_2["created"] == datetime(1971, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()
    assert dict_2["fieldParcelIds"] == ["1111111111"]
    assert dict_2["compositionId"] == "aecea423-a08a-4a33-8a11-18dfb13f171c"

    modifications = dict_2["modified"]
    assert len(modifications) == 2

    assert modifications[0]["modificationType"] == "PROJECT_UPDATE"
    assert modifications[0]["datetime"] == datetime(1971, 1, 2, 0, 0, tzinfo=timezone.utc).isoformat()

    assert modifications[1]["modificationType"] == "WEATHER_UPDATE"
    assert modifications[1]["datetime"] == datetime(1971, 1, 3, 0, 0, tzinfo=timezone.utc).isoformat()


def test_save(subproject_json_2: Path):
    tempdir = tempfile.TemporaryDirectory()
    temp_path = Path(tempdir.name)
    subproject_path = temp_path / "subproject"

    shutil.copy(subproject_json_2, subproject_path)
    subproject = Subproject.from_json(subproject_path)
    subproject.save()

    expected_2 = """{
    "id": "0069d09b-890a-4d1a-8922-d3b0fc8342b1",
    "name": "test_subproject_3",
    "fieldParcelIds": [
        "1111111111"
    ],
    "compositionId": "aecea423-a08a-4a33-8a11-18dfb13f171c",
    "created": "1971-01-01T00:00:00+00:00",
    "modified": [
        {
            "modificationType": "PROJECT_UPDATE",
            "datetime": "1971-01-02T00:00:00+00:00"
        },
        {
            "modificationType": "WEATHER_UPDATE",
            "datetime": "1971-01-03T00:00:00+00:00"
        }
    ]
}"""

    assert subproject.json_config_path().read_text() == expected_2


def test_export_user_data_to_csv(subproject_with_data_folder: Path):
    tempdir = tempfile.TemporaryDirectory()
    temp_path = Path(tempdir.name)
    subproject_path = temp_path / "subproject"

    shutil.copytree(subproject_with_data_folder, subproject_path)
    subproject = Subproject.from_json(subproject_path / "peltomappi_subproject.json")
    subproject.export_user_data_to_csv(())

    assert subproject.tables_directory().exists()

    csv = subproject.tables_directory() / "data.csv"

    assert csv.exists()

    expected = """,PERUSLOHKOTUNNUS,x,y
0,1111111111,500.0,-500.0
1,2222222222,8500.0,500.0
2,3333333333,7500.0,-6500.0
3,4444444444,500.0,-7500.0
"""

    with open(csv, "r") as file:
        assert file.read() == expected
