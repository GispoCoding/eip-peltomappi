from pathlib import Path
from osgeo import gdal, ogr, osr

PELTOMAPPI_CONFIG_LAYER_NAME = "__peltomappi_config"


class ConfigError(Exception):
    pass


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
            ConfigError: If any check fails.
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
