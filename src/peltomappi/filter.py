from pathlib import Path
import shutil
import sqlite3
import tempfile
from uuid import uuid4

from geopandas import gpd, pd
from shapely.geometry import Polygon

from peltomappi.logger import LOGGER

FIELD_PARCEL_IDENTIFIER_COLUMN = "peruslohkotunnus"


class FilterError(Exception):
    pass


def get_spatial_filter_from_field_parcel_ids(
    field_parcel_dataset: Path,
    field_parcel_ids: set[str],
    *,
    buffer_distance: float = 1000,
) -> Polygon:
    """
    Returns:
        a shapely (Multi)Polygon, buffered around the field parcels, identified by the given IDs
    """
    filter_tuple_innards = ", ".join(f"'{id}'" for id in field_parcel_ids)
    where_clause: str = f"{FIELD_PARCEL_IDENTIFIER_COLUMN} IN ({filter_tuple_innards})"
    field_parcel_gdf: gpd.GeoDataFrame = gpd.read_file(
        field_parcel_dataset,
        columns=[FIELD_PARCEL_IDENTIFIER_COLUMN],
        engine="pyogrio",
        where=where_clause,
    )

    series = pd.Series([id for id in field_parcel_ids])
    if not field_parcel_gdf[FIELD_PARCEL_IDENTIFIER_COLUMN].isin(series).all:
        msg = "unexpected ids found in filtered dataset"
        raise FilterError(msg)

    return field_parcel_gdf.geometry.union_all().buffer(buffer_distance)


def spatial_filter(
    input_path: Path,
    output_path: Path,
    spatial_filter: Polygon,
    *,
    overwrite: bool = False,
) -> None:
    """
    Reads an input dataset from the path, filters it according to the spatial
    filter and writes the filtered dataset to a GeoPackage file.

    Args:
        input_path: Path to a geospatial dataset that can be opened with GeoPandas.
        output_path: Path to the output GeoPackage
        spatial_filter: shapely (Multi)Polygon, features intersecting this will be included in the output
        overwrite: (optional) whether the output file can be overwritten

    """

    # TODO: test this better

    if not overwrite and output_path.exists():
        msg = f"attempting to write file {output_path} but it already exists and overwrite has not been permitted"
        raise FilterError(msg)

    # if the input dataset has a geometry that includes an M value this gives a
    # warning that it has been changed, in reality it hasn't permanently
    # changed anything and the warning can be disregarded
    layers = gpd.list_layers(input_path)

    if len(layers.index) > 1:
        msg = "filtering dataset with multiple layers not supported currently"
        raise FilterError(msg)

    layer_name = layers["name"].item()

    filtered_gdf: gpd.GeoDataFrame = gpd.read_file(
        input_path,
        engine="pyogrio",
        mask=spatial_filter,
    )

    if len(filtered_gdf.index) == 0:
        LOGGER.warning("Filtered GeoDataFrame is empty!")
        # FIXME: if this happens, the geometry type of the output gpkg will be
        # unknown, breaking QGIS layers see comments in copy_gpkg_as_empty()

    filtered_gdf.to_file(
        output_path,
        driver="GPKG",
        layer=layer_name,
    )


def filter_gpkg_by_field_parcel_ids(
    input_path: Path,
    output_path: Path,
    field_parcel_ids: list[str],
    *,
    overwrite: bool = False,
) -> None:
    """
    Reads an input field parcel dataset, filters it and saves to new location
    """

    # TODO: test

    if not overwrite and output_path.exists():
        msg = f"attempting to write file {output_path} but it already exists and overwrite has not been permitted"
        raise FilterError(msg)

    filter_tuple_innards = ", ".join(f"'{id}'" for id in field_parcel_ids)
    where_clause: str = f'"{FIELD_PARCEL_IDENTIFIER_COLUMN}" IN ({filter_tuple_innards})'
    field_parcel_gdf: gpd.GeoDataFrame = gpd.read_file(
        input_path,
        engine="pyogrio",
        where=where_clause,
    )

    series = pd.Series([id for id in field_parcel_ids])
    if not field_parcel_gdf[FIELD_PARCEL_IDENTIFIER_COLUMN].isin(series).all:
        msg = "unexpected ids found in filtered dataset"
        raise FilterError(msg)

    if len(field_parcel_gdf.index) == 0:
        LOGGER.warning("Filtered GeoDataFrame is empty!")

    field_parcel_gdf.to_file(output_path)


def copy_gpkg_as_empty(
    input_path: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
) -> None:
    """
    Reads an input dataset from the path and creates an empty version of it at the
    output path.
    """

    # TODO: test this better

    if not overwrite and output_path.exists():
        msg = f"attempting to write file {output_path} but it already exists and overwrite has not been permitted"
        raise FilterError(msg)

    # HACK: kind of a hack, at least currently where this is mixed with
    # using geopandas, but doing this is necessary because geopandas IO
    # does not work well with empty / non-geometric tables
    # maybe just use sqlite3 to do the filtering as well? geopandas is a bit
    # overkill anyway, at least for what it's used for right now

    tempdir = tempfile.TemporaryDirectory()
    temp_file_path = Path(tempdir.name) / str(uuid4())

    shutil.copy(input_path, temp_file_path)

    with sqlite3.connect(temp_file_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

        # HACK: this is not airtight
        tables = [
            table[0]
            for table in cursor.fetchall()
            if not table[0].startswith("gpkg_")
            and not table[0].startswith("rtree_")
            and not table[0].startswith("sqlite_")
        ]

        # if len(tables) > 1:
        #     msg = "filtering dataset with multiple layers not supported currently"
        #     raise FilterError(msg)

        for table in tables:
            cursor.execute(f'DELETE FROM "{table}";')

    with sqlite3.connect(temp_file_path) as conn:
        cursor = conn.cursor()
        cursor.execute("VACUUM;")

    shutil.move(temp_file_path, output_path)
