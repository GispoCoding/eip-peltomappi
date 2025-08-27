import logging
from pathlib import Path
from typing import NamedTuple

from osgeo import gdal, ogr, osr
from tqdm import tqdm

from peltomappi.config import Config
from peltomappi.logger import LOGGER
from peltomappi.utils import config_description_to_path

PELTOMAPPI_CONFIG_LAYER_NAME = "__peltomappi_config"


class DivisionResult(NamedTuple):
    folders: tuple[Path, ...]
    files: tuple[Path, ...]


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
    __overwrite: bool

    def __init__(
        self,
        *,
        input_dataset: Path,
        output_dir: Path,
        config: Config,
        filename: str,
        layer_filter: tuple[str] | None = None,
        overwrite: bool = False,
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
            overwrite: whether divider is allowed to overwrite files
        """

        self.__input_dataset = input_dataset
        self.__output_directory = output_dir
        self.__config = config
        self.__filename = filename
        self.__layer_filter = layer_filter
        self.__overwrite = overwrite

    @staticmethod
    def divide_layer(
        *,
        in_layer: ogr.Layer,
        area: ogr.Geometry,
        output_dataset: ogr.DataSource,
    ):
        in_layer.SetSpatialFilter(area)
        in_layer_defn: ogr.FeatureDefn = in_layer.GetLayerDefn()

        in_layer_total_features = in_layer.GetFeatureCount(1)

        if in_layer_total_features == 0:
            LOGGER.info(f"Layer {in_layer.GetName()} has zero features in this area!")

        out_layer_name = in_layer.GetName()

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

    @staticmethod
    def divide_into_area(
        *,
        input_path: Path,
        output_path: Path,
        area: ogr.Geometry,
        overwrite: bool = False,
    ):
        if not overwrite and output_path.exists():
            msg = f"attempting to write file {output_path} but it already exists and overwrite has not been permitted"
            raise DividerError(msg)

        input_dataset: gdal.Dataset = gdal.OpenEx(
            input_path,
            gdal.OF_VECTOR | gdal.OF_READONLY,
        )

        if not input_dataset:
            msg = f"Could not open dataset from {input_dataset}"
            raise DividerError(msg)

        out_driver: ogr.Driver = ogr.GetDriverByName("GPKG")
        output_dataset: ogr.DataSource = out_driver.CreateDataSource(output_path)

        for i in range(0, input_dataset.GetLayerCount()):
            in_layer: ogr.Layer = input_dataset.GetLayerByIndex(i)

            Divider.divide_layer(in_layer=in_layer, area=area, output_dataset=output_dataset)

            LOGGER.info(
                f"Layer saved to {output_path}|layername={in_layer.GetName()}",
            )

    def divide(self) -> DivisionResult:
        """
        Performs the division based on the set state.

        Raises:
            DividerError: indirectly, if input dataset could not be opened.
        """
        # TODO: get rid of this function and make divider purely a container of static functions
        # and write docstrings for the new functions
        files = []
        folders = []

        for description, filter_geom in self.__config.to_dict().items():
            area_directory = config_description_to_path(description, self.__output_directory)
            area_directory.mkdir(exist_ok=True)

            folders.append(area_directory)

            output_gpkg: Path = area_directory / f"{self.__filename}.gpkg"
            files.append(output_gpkg)

            Divider.divide_into_area(
                input_path=self.__input_dataset,
                output_path=output_gpkg,
                area=filter_geom,
                overwrite=self.__overwrite,
            )

        return DivisionResult(
            folders=tuple(folders),
            files=tuple(files),
        )
