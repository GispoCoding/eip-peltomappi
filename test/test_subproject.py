from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from geopandas import gpd

from peltomappi.filter import FIELD_PARCEL_IDENTIFIER_COLUMN
from peltomappi.subproject import (
    TEMPLATE_MERGIN_CONFIG_NAME,
    TEMPLATE_QGIS_PROJECT_NAME,
    ModificationAction,
    ModificationType,
    Subproject,
    SubprojectError,
)

import pytest

import tempfile


def test_from_subproject_json(
    subproject_json_1: Path,
    subproject_json_2: Path,
    subproject_json_3: Path,
):
    subproject_1 = Subproject.from_json(subproject_json_1)
    assert subproject_1.id() is None
    assert subproject_1.name() == "test_subproject_1"
    assert subproject_1.path() is None
    assert subproject_1.field_parcel_ids() == ["2222222222", "3333333333"]
    assert subproject_1.created() is None
    assert subproject_1.modified() is None
    assert subproject_1.composition_id() is None

    subproject_2 = Subproject.from_json(subproject_json_2)
    assert subproject_2.id() == UUID("30bf748e-6dab-4dcd-95ea-9903c6524150")
    assert subproject_2.name() == "test_subproject_2"
    assert subproject_2.path() == Path("/somewhere")
    assert subproject_2.field_parcel_ids() == ["1111111111", "2222222222"]
    assert subproject_2.created() == datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert subproject_2.modified() is None
    assert subproject_2.composition_id() == UUID("234634d0-7b02-4634-b520-1dc0331dd2bc")

    subproject_3 = Subproject.from_json(subproject_json_3)
    assert subproject_3.id() == UUID("0069d09b-890a-4d1a-8922-d3b0fc8342b1")
    assert subproject_3.name() == "test_subproject_3"
    assert subproject_3.path() == Path("/somewhere/else")
    assert subproject_3.field_parcel_ids() == ["1111111111"]
    assert subproject_3.created() == datetime(1971, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert subproject_3.modified() == [
        ModificationAction(
            mod_type=ModificationType.PROJECT_UPDATE, timestamp=datetime(1971, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
        ),
        ModificationAction(
            mod_type=ModificationType.WEATHER_UPDATE, timestamp=datetime(1971, 1, 3, 0, 0, 0, tzinfo=timezone.utc)
        ),
    ]
    assert subproject_3.composition_id() == UUID("aecea423-a08a-4a33-8a11-18dfb13f171c")


def test_create(
    subproject_json_1: Path,
    subproject_json_2: Path,
    test_template_project: Path,
    test_full_data: Path,
):
    tempdir = tempfile.TemporaryDirectory()
    temp_path_1 = Path(tempdir.name) / "subproject1"
    temp_path_2 = Path(tempdir.name) / "subproject2"

    composition_id = UUID("cba6cbe5-61a0-4a0e-92db-a53575e7785e")

    subproject_1 = Subproject.from_json(subproject_json_1)
    subproject_1.create(
        test_template_project,
        temp_path_1,
        test_full_data,
        composition_id,
    )

    assert not (temp_path_1 / "proj").exists()
    assert not (temp_path_1 / "dummy.gpkg-wal").exists()
    assert not (temp_path_1 / "dummy.gpkg-shm").exists()
    assert (temp_path_1 / TEMPLATE_QGIS_PROJECT_NAME).exists()
    assert (temp_path_1 / TEMPLATE_MERGIN_CONFIG_NAME).exists()

    parcels_2023 = temp_path_1 / "peltolohkot_2023.gpkg"
    parcels_2024 = temp_path_1 / "peltolohkot_2024.gpkg"

    assert parcels_2023.exists()
    gdf_2023: gpd.GeoDataFrame = gpd.read_file(parcels_2023)
    assert len(gdf_2023.index) == 2
    assert gdf_2023.iloc[0][FIELD_PARCEL_IDENTIFIER_COLUMN] == "2222222222"
    assert gdf_2023.iloc[1][FIELD_PARCEL_IDENTIFIER_COLUMN] == "3333333333"

    assert parcels_2024.exists()
    gdf_2024: gpd.GeoDataFrame = gpd.read_file(parcels_2024)
    assert len(gdf_2024.index) == 2
    assert gdf_2024.iloc[0][FIELD_PARCEL_IDENTIFIER_COLUMN] == "2222222222"
    assert gdf_2024.iloc[1][FIELD_PARCEL_IDENTIFIER_COLUMN] == "3333333333"

    assert subproject_1.id() is not None
    assert subproject_1.path() is not None
    assert subproject_1.created() is not None
    assert subproject_1.modified() is not None
    assert subproject_1.composition_id() is not None

    # can't really predict these so next best thing is to check they are set to
    # something and are the correct type
    assert isinstance(subproject_1.id(), UUID)
    assert isinstance(subproject_1.created(), datetime)

    assert subproject_1.name() == "test_subproject_1"
    assert subproject_1.path() == temp_path_1
    assert subproject_1.modified() == []
    assert subproject_1.composition_id() == composition_id

    # a bit redundant, but might as well check that this wasn't somehow
    # modified
    assert subproject_1.field_parcel_ids() == ["2222222222", "3333333333"]

    subproject_2 = Subproject.from_json(subproject_json_2)
    with pytest.raises(SubprojectError):
        subproject_2.create(
            test_template_project,
            temp_path_2,
            test_full_data,
            composition_id,
        )


def test_to_json_dict(
    subproject_json_2: Path,
    subproject_json_3: Path,
):
    subproject_2 = Subproject.from_json(subproject_json_2)
    dict_2 = subproject_2.to_json_dict()
    assert dict_2["id"] == "30bf748e-6dab-4dcd-95ea-9903c6524150"
    assert dict_2["name"] == "test_subproject_2"
    assert dict_2["created"] == datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()
    assert dict_2["fieldParcelIds"] == ["1111111111", "2222222222"]
    assert dict_2["path"] == "/somewhere"
    assert dict_2.get("modified") is None
    assert dict_2["compositionId"] == "234634d0-7b02-4634-b520-1dc0331dd2bc"

    subproject_3 = Subproject.from_json(subproject_json_3)
    dict_3 = subproject_3.to_json_dict()
    assert dict_3["id"] == "0069d09b-890a-4d1a-8922-d3b0fc8342b1"
    assert dict_3["name"] == "test_subproject_3"
    assert dict_3["created"] == datetime(1971, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()
    assert dict_3["fieldParcelIds"] == ["1111111111"]
    assert dict_3["path"] == "/somewhere/else"
    assert dict_3["compositionId"] == "aecea423-a08a-4a33-8a11-18dfb13f171c"

    modifications = dict_3["modified"]
    assert len(modifications) == 2

    assert modifications[0]["modificationType"] == "PROJECT_UPDATE"
    assert modifications[0]["datetime"] == datetime(1971, 1, 2, 0, 0, tzinfo=timezone.utc).isoformat()

    assert modifications[1]["modificationType"] == "WEATHER_UPDATE"
    assert modifications[1]["datetime"] == datetime(1971, 1, 3, 0, 0, tzinfo=timezone.utc).isoformat()
