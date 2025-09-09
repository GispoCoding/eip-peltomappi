from pathlib import Path
import shutil

from geopandas import gpd, pd
from shapely.geometry import Polygon

FIELD_PARCEL_IDENTIFIER_COLUMN = "PERUSLOHKOTUNNUS"
DEFAULT_IDENTIFIED_FIELD_PARCEL_BUFFER_DISTANCE_METERS = 1000


class FilterError(Exception):
    pass


def get_spatial_filter_from_field_parcel_ids(
    field_parcel_dataset: Path,
    field_parcel_ids: set[str],
    *,
    buffer_distance: float = DEFAULT_IDENTIFIED_FIELD_PARCEL_BUFFER_DISTANCE_METERS,
) -> Polygon:
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


def filter_dataset_by_field_parcel_ids(
    input_path: Path,
    output_path: Path,
    spatial_filter: Polygon,
    *,
    overwrite: bool = False,
):
    """ """
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

    # HACK: terrible way of doing this sustainably and does not belong here at
    # all
    if layer_name in (
        "tracking_layer",
        "kohteet",
        "maapera",
        "mara_kerros",
        "mara_kuoppa",
        "penetrometri",
    ):
        shutil.copy(input_path, output_path)
        return

    filtered_gdf: gpd.GeoDataFrame = gpd.read_file(
        input_path,
        engine="pyogrio",
        mask=spatial_filter,
    )

    filtered_gdf.to_file(
        output_path,
        driver="GPKG",
        layer=layer_name,
    )
