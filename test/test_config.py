from pathlib import Path

import tempfile

from geopandas import gpd, testing

from peltomappi.config import convert_config_json_to_gpkg


def test_convert_config_json_to_gpkg(
    config_json: Path,
    fulldata: Path,
    config_gpkg: Path,
):
    temp_dir = tempfile.TemporaryDirectory()
    output = Path(temp_dir.name) / "output.gpkg"

    convert_config_json_to_gpkg(
        config_json,
        output,
        fulldata,
        buffer_distance=1,
    )

    gdf = gpd.read_file(output)
    expected_gdf = gpd.read_file(config_gpkg)

    testing.assert_geodataframe_equal(gdf, expected_gdf)
