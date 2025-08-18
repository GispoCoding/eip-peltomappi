from enum import Enum
import logging
from pathlib import Path

import click
from tqdm import tqdm

from osgeo import gdal, ogr

from peltomappi.logger import LOGGER


class DownloadError(Exception):
    pass


class Downloader:
    class Type(Enum):
        UNKNOWN = 0
        FIELD_PARCEL = 1
        GROUNDWATER_AREA = 2

        @staticmethod
        def to_choice() -> click.Choice:
            return click.Choice(
                [option.name for option in Downloader.Type][1:],
            )

    download_type: Type = Type.UNKNOWN
    output_directory: Path
    FIELD_PARCEL_LINK = "https://inspire.ruokavirasto-awsa.com/geoserver/wfs?request=GetCapabilities"

    def __init__(self, download_type: Type, output_dir: Path) -> None:
        self.download_type = download_type
        self.output_directory = output_dir

    def __download_field_parcel(self) -> None:
        input_dataset = gdal.OpenEx(
            self.FIELD_PARCEL_LINK,
            gdal.OF_VECTOR | gdal.OF_READONLY,
        )

        output_gpkg: Path = self.output_directory / "peltolohkot.gpkg"
        out_driver: ogr.Driver = ogr.GetDriverByName("GPKG")
        output_dataset: ogr.DataSource = out_driver.CreateDataSource(output_gpkg)

        years = (
            2020,
            2021,
            2022,
            2023,
            2024,
        )

        filter_geom = ogr.CreateGeometryFromWkt(
            "POLYGON ((472611.71926543978042901 7028778.47905620466917753, "
            "482527.46018222777638584 7028778.47905620466917753, "
            "482527.46018222777638584 7032983.30365468841046095, "
            "472611.71926543978042901 7032983.30365468841046095, "
            "472611.71926543978042901 7028778.47905620466917753))",
        )

        layer_prefix = "LandUse.ExistingLandUse.GSAAAgriculturalParcel."
        for year in years:
            in_layer_name = f"{layer_prefix}{year}"
            out_layer_name = f"peltolohko_{year}"

            in_layer: ogr.Layer = input_dataset.GetLayerByName(in_layer_name)

            if in_layer is None:
                msg = f'Layer "{in_layer_name}" was not found'
                raise DownloadError(msg)

            LOGGER.info(f"Processing {in_layer_name}")

            in_layer.SetSpatialFilter(filter_geom)
            in_layer_defn: ogr.FeatureDefn = in_layer.GetLayerDefn()

            out_layer: ogr.Layer = output_dataset.CreateLayer(
                out_layer_name,
                geom_type=in_layer_defn.GetGeomType(),
            )

            for i in range(0, in_layer_defn.GetFieldCount()):
                field_defn = in_layer_defn.GetFieldDefn(i)

                out_layer.CreateField(field_defn)

            progress_total = 0
            show_progress = LOGGER.level < logging.WARNING

            if show_progress:
                progress_total = in_layer.GetFeatureCount()

            in_feature: ogr.Feature
            for in_feature in tqdm(
                in_layer,
                total=progress_total,
                leave=False,
                disable=not show_progress,
            ):
                out_layer.CreateFeature(in_feature.Clone())

            LOGGER.info(f"Layer saved to {output_gpkg}|layername={out_layer_name}")

    def __download_groundwater_area(self) -> None:
        LOGGER.info(f"Downloading GroundWaterAreas to {self.output_directory}")

    def run(self) -> None:
        if self.download_type == Downloader.Type.UNKNOWN:
            msg = "Unknown download type"
            raise DownloadError(msg)
        elif self.download_type == Downloader.Type.FIELD_PARCEL:
            self.__download_field_parcel()
        elif self.download_type == Downloader.Type.GROUNDWATER_AREA:
            self.__download_groundwater_area()
        else:
            msg = "Unhandled download type"
            raise DownloadError(msg)
