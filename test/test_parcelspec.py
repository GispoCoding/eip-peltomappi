from datetime import datetime
import json
from pathlib import Path
from uuid import UUID

from freezegun import freeze_time
from geopandas import gpd


from peltomappi.filter import FIELD_PARCEL_IDENTIFIER_COLUMN
from peltomappi.parcelspec import ParcelSpecification


import tempfile

from peltomappi.subproject import SUBPROJECT_CONFIG_NAME, TEMPLATE_MERGIN_CONFIG_NAME, TEMPLATE_QGIS_PROJECT_NAME


def test_from_json(
    parcel_spec: Path,
):
    ps = ParcelSpecification.from_json(parcel_spec)
    assert ps.name() == "test_parcelspec"
    assert ps.field_parcel_ids() == [
        "2222222222",
        "3333333333",
    ]


@freeze_time("1970-01-01 00:00:00")
def test_to_subproject(
    parcel_spec: Path,
    test_template_project: Path,
    test_full_data: Path,
):
    tempdir = tempfile.TemporaryDirectory()
    temp_path = Path(tempdir.name) / "subproject1"

    composition_id = UUID("cba6cbe5-61a0-4a0e-92db-a53575e7785e")

    ps = ParcelSpecification.from_json(parcel_spec)
    subproject = ps.to_subproject(
        test_template_project,
        temp_path,
        test_full_data,
        composition_id,
    )

    assert not (temp_path / "proj").exists()
    assert not (temp_path / "dummy.gpkg-wal").exists()
    assert not (temp_path / "dummy.gpkg-shm").exists()
    assert (temp_path / TEMPLATE_QGIS_PROJECT_NAME).exists()
    assert (temp_path / TEMPLATE_MERGIN_CONFIG_NAME).exists()

    saved_subproject = temp_path / SUBPROJECT_CONFIG_NAME

    assert saved_subproject.exists()
    assert json.loads(saved_subproject.read_text()) == subproject.to_json_dict()

    parcels_2023 = temp_path / "data/Peltolohkot_2023.gpkg"
    parcels_2024 = temp_path / "data/Peltolohkot_2024.gpkg"

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

    assert subproject.id() is not None
    assert subproject.path() is not None
    assert subproject.created() is not None
    assert subproject.modified() is not None
    assert subproject.composition_id() is not None

    # can't really predict this so next best thing is to check it is set to
    # something and is the correct type
    assert isinstance(subproject.id(), UUID)

    assert subproject.name() == "test_parcelspec"
    assert subproject.path() == temp_path
    assert subproject.modified() == []
    assert subproject.composition_id() == composition_id
    assert subproject.created() == datetime.fromtimestamp(0)

    # a bit redundant, but might as well check that this wasn't somehow
    # modified
    assert subproject.field_parcel_ids() == ["2222222222", "3333333333"]
