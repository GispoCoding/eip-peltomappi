import logging
from pathlib import Path
from typing import Callable

from osgeo import gdal, ogr, osr
from tqdm import tqdm

from peltomappi.config import Config
from peltomappi.logger import LOGGER
from peltomappi.utils import clean_string_to_filename

PELTOMAPPI_CONFIG_LAYER_NAME = "__peltomappi_config"


class DividerError(Exception):
    pass


class Divider:
    """
    Class for executing division of spatial data i.e. reading in a larger
    dataset and dividing it to smaller parts using a spatial filter.
    """

    __input_dataset: Path
    __output_directory: Path
    __config: Config
    __filename: str
    __layer_filter: tuple[str] | None
    __layer_name_callback: Callable[[str], str] | None
    __delete_empty: bool

    def __init__(
        self,
        *,
        input_dataset: Path,
        output_dir: Path,
        config: Config,
        filename: str,
        layer_filter: tuple[str] | None = None,
        layer_name_callback: Callable[[str], str] | None = None,
        delete_empty: bool = False,
    ) -> None:
        """
        Sets state for Divider.

        Args:
            input_dataset: path to the input dataset
            output_dir: output directory for divided GeoPackages
            config: configuration object
            filename: filename of divided GPKG
            layer_filter: optional layer filter
            layer_name_callback: optional callable to modify output layer names
            delete_empty: whether to include empty layers and output GPKGs
        """

        self.__input_dataset = input_dataset
        self.__output_directory = output_dir
        self.__config = config
        self.__filename = filename
        self.__layer_filter = layer_filter
        self.__layer_name_callback = layer_name_callback
        self.__delete_empty = delete_empty

    def divide(self) -> None:
        """
        Performs the division based on the set state.

        Raises:
            DividerError: if input dataset could not be opened.
        """
        config = self.__config.to_dict()

        input_dataset: gdal.Dataset = gdal.OpenEx(
            self.__input_dataset,
            gdal.OF_VECTOR | gdal.OF_READONLY,
        )

        if not input_dataset:
            msg = f"Could not open dataset from {self.__input_dataset}"
            raise DividerError(msg)

        for description, filter_geom in config.items():
            area_directory = Path(self.__output_directory / clean_string_to_filename(description).lower())
            area_directory.mkdir(exist_ok=True)

            output_gpkg: Path = area_directory / f"{self.__filename}.gpkg"

            out_driver: ogr.Driver = ogr.GetDriverByName("GPKG")
            output_dataset: ogr.DataSource = out_driver.CreateDataSource(output_gpkg)

            LOGGER.info(f"Dividing {description}.")

            for i in range(0, input_dataset.GetLayerCount()):
                in_layer: ogr.Layer = input_dataset.GetLayerByIndex(i)
                in_layer_name: str = in_layer.GetName()

                if self.__layer_filter is not None and in_layer_name not in self.__layer_filter:
                    continue

                LOGGER.info(f"Processing layer: {in_layer_name}")

                in_layer.SetSpatialFilter(filter_geom)
                in_layer_defn: ogr.FeatureDefn = in_layer.GetLayerDefn()

                in_layer_total_features = in_layer.GetFeatureCount(1)

                if self.__delete_empty and in_layer_total_features == 0:
                    LOGGER.info(f"Layer {in_layer_name} has zero features in {description}, skipping layer...")
                    continue

                out_layer_name = (
                    in_layer.GetName()
                    if self.__layer_name_callback is None
                    else self.__layer_name_callback(in_layer.GetName())
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

            if self.__delete_empty:
                total_output_layers = output_dataset.GetLayerCount()
                if total_output_layers == 0:
                    LOGGER.info(f"Output GeoPackage {output_gpkg} has zero layers, deleting...")
                    out_driver.DeleteDataSource(output_gpkg)
