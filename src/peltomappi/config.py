from pathlib import Path
from typing import Any
from osgeo import gdal, ogr, osr

from geopandas import gpd

import json


PELTOMAPPI_CONFIG_LAYER_NAME = "__peltomappi_config"
FIELD_PARCEL_IDENTIFIER_COLUMN = "PERUSLOHKOTUNNUS"
IDENTIFIED_FIELD_PARCEL_BUFFER_DISTANCE_METERS = 1000


class ConfigError(Exception):
    pass


def __validate_json_config(data: Any) -> dict[str, list[str]]:
    """
    Checks that data read from a JSON file is in the correct format.

    Raises:
        ConfigError: if any check fails

    Returns:
        the data unchanged, correctly typed
    """
    if not isinstance(data, dict):
        msg = "read json is not a dictionary"
        raise ConfigError(msg)

    for _list in data.values():
        if not isinstance(_list, list):
            msg = f"{_list} should be a list of strings"
            raise ConfigError(msg)

        for value in _list:
            if not isinstance(value, str):
                msg = f"value {value} in list should be a string"
                raise ConfigError(msg)

    return data


def convert_config_json_to_gpkg(
    input: Path,
    output: Path,
    data_gpkg: Path,
    *,
    overwrite: bool = False,
) -> None:
    """
    Converts a json to a valid peltomappi config.

    Args:
        input: path to the json file
        output: path of the output GeoPackage
        data_gpkg: path of a GeoPackage which contains field parcels

    Raises:
        ConfigError: if not all IDs exist in the data_gpkg, indirectly if input
            JSON is invalid
    """

    if not overwrite and output.exists():
        msg = f"file {output} exists and overwrite has not been permitted"
        raise ConfigError(msg)

    data = __validate_json_config(json.loads(input.read_text()))

    _ids: list[str] = []
    for _, items in data.items():
        _ids.extend(items)

    ids: set[str] = set(_ids)

    where_clause: str = f"{FIELD_PARCEL_IDENTIFIER_COLUMN} IN ({', '.join(ids)})"

    in_gdf: gpd.GeoDataFrame = gpd.read_file(
        data_gpkg,
        columns=[FIELD_PARCEL_IDENTIFIER_COLUMN],
        engine="pyogrio",
        where=where_clause,
    )

    if len(ids) != len(in_gdf.index):
        msg = "Number of given IDs does not match number of found IDs"
        raise ConfigError(msg)

    out_geometries = []
    out_descriptions = []
    for person, field_parcel_ids in data.items():
        parcel: gpd.GeoSeries = in_gdf.loc[in_gdf[FIELD_PARCEL_IDENTIFIER_COLUMN].isin(field_parcel_ids)]

        multi_geom = parcel.geometry.union_all().buffer(IDENTIFIED_FIELD_PARCEL_BUFFER_DISTANCE_METERS)

        out_descriptions.append(person)
        out_geometries.append(multi_geom)

    out_gdf = gpd.GeoDataFrame(
        {
            "description": out_descriptions,
        },
        geometry=out_geometries,
        crs=in_gdf.crs,
    )

    out_gdf.to_file(output, layer="__peltomappi_config")


class Config:
    """
    Class for dealing with project/division configuration.
    """

    __gpkg_path: Path

    def __init__(self, gpkg_path: Path):
        """
        Sets state for Config and validates file.

        Args:
            gpkg_path: path to the GeoPackage containing config options

        Raises:
            ConfigError: if config GPKG is invalid
        """
        self.__gpkg_path = gpkg_path
        self.__validate_config_layer()

    def path(self) -> Path:
        """
        Returns:
            Path: of configuration GeoPackage
        """
        return self.__gpkg_path

    def __validate_config_layer(self) -> None:
        """
        Performs a series of validation checks of a configuration layer.
        The configuration layer must fulfill these requirements:
            - geometry type is polygon or multipolygon
            - CRS is EPSG:3067
            - has exactly 1 field
            - the field must be called "description"
            - the field must be of type "string"
            - the layer cannot be empty
            - no feature can have a null description
            - description must be unique to each feature

        Raises:
            ConfigError: if any check fails
        """
        config_dataset: ogr.DataSource = gdal.OpenEx(
            self.__gpkg_path,
            gdal.OF_VECTOR | gdal.OF_READONLY,
        )

        layer: ogr.Layer = config_dataset.GetLayerByName(PELTOMAPPI_CONFIG_LAYER_NAME)

        if layer is None:
            msg = f"{PELTOMAPPI_CONFIG_LAYER_NAME} layer not found!"
            raise ConfigError(msg)

        layer_defn: ogr.FeatureDefn = layer.GetLayerDefn()

        acceptable_geom_types = (
            ogr.wkbPolygon,
            ogr.wkbMultiPolygon,
        )

        if layer_defn.GetGeomType() not in acceptable_geom_types:
            msg = f"config layer has unacceptable geometry type: {ogr.GeometryTypeToName(layer_defn.GetGeomType())}!"
            raise ConfigError(msg)

        crs: osr.SpatialReference = layer.GetSpatialRef()
        if not (crs.GetAuthorityName(None) == "EPSG" and crs.GetAuthorityCode(None) == "3067"):
            msg = f"config layer has unacceptable CRS: {crs.GetAuthorityName(None)}:{crs.GetAuthorityCode(None)}"
            raise ConfigError(msg)

        if layer_defn.GetFieldCount() != 1:
            msg = "config layer has to have exactly 1 field"
            raise ConfigError(msg)

        description_field_defn: ogr.FieldDefn = layer_defn.GetFieldDefn(0)
        field_name: str = description_field_defn.GetName()

        if field_name != "description":
            msg = "config layer must have a field called description"
            raise ConfigError(msg)

        if description_field_defn.GetType() != ogr.OFTString:
            msg = f"description field must be of type string, not {description_field_defn.GetTypeName()}"
            raise ConfigError(msg)

        if layer.GetFeatureCount(True) == 0:
            msg = "config layer has no features"
            raise ConfigError(msg)

        descriptions = set()

        feature: ogr.Feature
        for feature in layer:
            description: str = feature.GetFieldAsString(0)

            if not description:
                msg = "null description found!"
                raise ConfigError(msg)

            descriptions.add(description)

        if len(descriptions) != layer.GetFeatureCount():
            msg = "duplicate description found!"
            raise ConfigError(msg)

    def to_dict(self) -> dict[str, ogr.Geometry]:
        """
        Reads configuration from GeoPackage and returns a dictionary based on
        it.

        Returns:
            Dictionary with the descriptions as keys and filter geometries as
            values.
        """
        config_dataset: ogr.DataSource = gdal.OpenEx(
            self.__gpkg_path,
            gdal.OF_VECTOR | gdal.OF_READONLY,
        )

        config_layer: ogr.Layer = config_dataset.GetLayerByName(PELTOMAPPI_CONFIG_LAYER_NAME)

        result: dict[str, ogr.Geometry] = {}

        feature: ogr.Feature
        for feature in config_layer:
            description: str = feature.GetFieldAsString(0)

            geom: ogr.Geometry = feature.GetGeometryRef()
            result[description] = geom.Clone()

        return result

    def descriptions(self) -> tuple[str, ...]:
        return tuple(self.to_dict().keys())
