import logging
from pathlib import Path
from typing import Callable

from osgeo import gdal, ogr, osr
from tqdm import tqdm

from peltomappi.logger import LOGGER
from peltomappi.utils import clean_string_to_filename

PELTOMAPPI_CONFIG_LAYER_NAME = "__peltomappi_config"


class DividerError(Exception):
    pass


class DividerConfigError(Exception):
    pass


class Divider:
    """
    Class for executing division of spatial data i.e. reading in a larger
    dataset and dividing it to smaller parts using a spatial filter.
    """

    input_dataset: Path
    output_directory: Path
    config_gpkg: Path
    filename_prefix: str
    layer_filter: tuple[str] | None
    layer_name_callback: Callable[[str], str] | None
    delete_empty: bool

    def __init__(
        self,
        *,
        input_dataset: Path,
        output_dir: Path,
        config_gpkg: Path,
        filename_prefix: str,
        layer_filter: tuple[str] | None = None,
        layer_name_callback: Callable[[str], str] | None = None,
        delete_empty: bool = False,
    ) -> None:
        """
        Sets state for divider.

        Args:
            input_dataset: path to the input dataset
            output_dir: output directory for divided GeoPackages
            config_gpkg: path to a configuration GeoPackage
            filename_prefix: prefix for divided GeoPackages' filenames
            layer_filter: optional layer filter
            layer_name_callback: optional callable to modify output layer names
            delete_empty: skip empty layers and delete empty divisions?
        """

        self.input_dataset = input_dataset
        self.output_directory = output_dir
        self.config_gpkg = config_gpkg
        self.filename_prefix = filename_prefix
        self.layer_filter = layer_filter
        self.layer_name_callback = layer_name_callback
        self.delete_empty = delete_empty

    @staticmethod
    def validate_config_layer(layer: ogr.Layer | None) -> None:
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
            DividerConfigError: If any check fails.
        """

        if layer is None:
            msg = f"{PELTOMAPPI_CONFIG_LAYER_NAME} layer not found!"
            raise DividerConfigError(msg)

        layer_defn: ogr.FeatureDefn = layer.GetLayerDefn()

        acceptable_geom_types = (
            ogr.wkbPolygon,
            ogr.wkbMultiPolygon,
        )

        if layer_defn.GetGeomType() not in acceptable_geom_types:
            msg = f"config layer has unacceptable geometry type: {ogr.GeometryTypeToName(layer_defn.GetGeomType())}!"
            raise DividerConfigError(msg)

        crs: osr.SpatialReference = layer.GetSpatialRef()
        if not (crs.GetAuthorityName(None) == "EPSG" and crs.GetAuthorityCode(None) == "3067"):
            msg = f"config layer has unacceptable CRS: {crs.GetAuthorityName(None)}:{crs.GetAuthorityCode(None)}"
            raise DividerConfigError(msg)

        if layer_defn.GetFieldCount() != 1:
            msg = "config layer has to have exactly 1 field"
            raise DividerConfigError(msg)

        description_field_defn: ogr.FieldDefn = layer_defn.GetFieldDefn(0)
        field_name: str = description_field_defn.GetName()

        if field_name != "description":
            msg = "config layer must have a field called description"
            raise DividerConfigError(msg)

        if description_field_defn.GetType() != ogr.OFTString:
            msg = f"description field must be of type string, not {description_field_defn.GetTypeName()}"
            raise DividerConfigError(msg)

        if layer.GetFeatureCount(True) == 0:
            msg = "config layer has no features"
            raise DividerConfigError(msg)

        descriptions = set()

        feature: ogr.Feature
        for feature in layer:
            description: str = feature.GetFieldAsString(0)

            if not description:
                msg = "null description found!"
                raise DividerConfigError(msg)

            descriptions.add(description)

        if len(descriptions) != layer.GetFeatureCount():
            msg = "duplicate description found!"
            raise DividerConfigError(msg)

    def __extract_config(self) -> dict[str, ogr.Geometry]:
        """
        Reads configuration from GeoPackage and returns a dictionary based on
        it.

        Returns:
            Dictionary with the descriptions as keys and filter geometries as
            values.

        Raises:
            DividerConfigError: indirectly if validate_config_layer() raises
            error
        """
        config_dataset: ogr.DataSource = gdal.OpenEx(
            self.config_gpkg,
            gdal.OF_VECTOR | gdal.OF_READONLY,
        )

        config_layer: ogr.Layer = config_dataset.GetLayerByName(PELTOMAPPI_CONFIG_LAYER_NAME)

        Divider.validate_config_layer(config_layer)

        result: dict[str, ogr.Geometry] = {}

        feature: ogr.Feature
        for feature in config_layer:
            description: str = feature.GetFieldAsString(0)

            geom: ogr.Geometry = feature.GetGeometryRef()
            result[description] = geom.Clone()

        return result

    def divide(self) -> None:
        """
        Performs the division based on the set state.

        Raises:
            DividerError: if input dataset could not be opened.
            DividerConfigError: indirectly, if configuration is invalid
        """
        config = self.__extract_config()

        input_dataset: gdal.Dataset = gdal.OpenEx(
            self.input_dataset,
            gdal.OF_VECTOR | gdal.OF_READONLY,
        )

        if not input_dataset:
            msg = f"Could not open dataset from {self.input_dataset}"
            raise DividerError(msg)

        for description, filter_geom in config.items():
            output_gpkg: Path = (
                self.output_directory / f"{self.filename_prefix}_{clean_string_to_filename(description).lower()}.gpkg"
            )

            out_driver: ogr.Driver = ogr.GetDriverByName("GPKG")
            output_dataset: ogr.DataSource = out_driver.CreateDataSource(output_gpkg)

            LOGGER.info(f"Dividing {description}.")

            for i in range(0, input_dataset.GetLayerCount()):
                in_layer: ogr.Layer = input_dataset.GetLayerByIndex(i)
                in_layer_name: str = in_layer.GetName()

                if self.layer_filter is not None and in_layer_name not in self.layer_filter:
                    continue

                LOGGER.info(f"Processing layer: {in_layer_name}")

                in_layer.SetSpatialFilter(filter_geom)
                in_layer_defn: ogr.FeatureDefn = in_layer.GetLayerDefn()

                in_layer_total_features = in_layer.GetFeatureCount(1)

                if self.delete_empty and in_layer_total_features == 0:
                    LOGGER.info(f"Layer {in_layer_name} has zero features in {description}, skipping layer...")
                    continue

                out_layer_name = (
                    in_layer.GetName()
                    if self.layer_name_callback is None
                    else self.layer_name_callback(in_layer.GetName())
                )

                crs: osr.SpatialReference = osr.SpatialReference()
                crs.ImportFromEPSG(3067)

                out_layer: ogr.Layer = output_dataset.CreateLayer(
                    out_layer_name,
                    crs,
                    geom_type=in_layer_defn.GetGeomType(),
                )

                for j in range(0, in_layer_defn.GetFieldCount()):
                    in_field_defn: ogr.FieldDefn = in_layer_defn.GetFieldDefn(j)
                    field_name: str = in_field_defn.GetNameRef()

                    in_field_defn.SetName(field_name.lower())

                    out_layer.CreateField(in_field_defn)

                show_progress = LOGGER.level < logging.WARNING

                out_layer_defn: ogr.FeatureDefn = out_layer.GetLayerDefn()
                in_feature: ogr.Feature
                for in_feature in tqdm(
                    in_layer,
                    total=in_layer_total_features,
                    leave=False,
                    disable=not show_progress,
                ):
                    out_feature = ogr.Feature(out_layer_defn)

                    for k in range(0, out_layer_defn.GetFieldCount()):
                        field_defn: ogr.FieldDefn = out_layer_defn.GetFieldDefn(k)
                        field_name = field_defn.GetName()

                        out_feature.SetField(
                            out_layer_defn.GetFieldDefn(k).GetNameRef(),
                            in_feature.GetField(k),
                        )

                    geom: ogr.Geometry = in_feature.GetGeometryRef()
                    out_feature.SetGeometry(geom.Clone())
                    out_layer.CreateFeature(out_feature)

                LOGGER.info(
                    f"Layer saved to {output_gpkg}|layername={out_layer_name}",
                )

            if self.delete_empty:
                total_output_layers = output_dataset.GetLayerCount()
                if total_output_layers == 0:
                    LOGGER.info(f"Output GeoPackage {output_gpkg} has zero layers, deleting...")
                    out_driver.DeleteDataSource(output_gpkg)
