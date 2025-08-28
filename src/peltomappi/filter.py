import logging
from pathlib import Path

from osgeo import gdal, ogr, osr
from tqdm import tqdm

from peltomappi.logger import LOGGER


class FilterError(Exception):
    pass


def filter_layer(
    *,
    in_layer: ogr.Layer,
    area: ogr.Geometry,
    output_dataset: ogr.DataSource,
):
    """
    Copies the input layer to an output dataset, filtering out features outside
    of the given area.

    Args:
        in_layer: input layer to be copied
        area: features outside this geometry are filtered out
        output_dataset: dataset the layer is copied to
    """
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


def filter_dataset(
    *,
    input_path: Path,
    output_path: Path,
    area: ogr.Geometry,
    overwrite: bool = False,
):
    """
    Filters the input dataset and writes a new output GeoPackage without the
    features outside of the given area.

    Args:
        input_path: uri of the input dataset
        output_path: path of the output GeoPackage
        area: features outside this geometry are filtered out
        overwrite: (optional) whether function can overwrite output file,
            defaults to False

    Returns:
        FilterError: if couldn't open input dataset or couldn't overwrite
            output
    """
    if not overwrite and output_path.exists():
        msg = f"attempting to write file {output_path} but it already exists and overwrite has not been permitted"
        raise FilterError(msg)

    input_dataset: gdal.Dataset = gdal.OpenEx(
        input_path,
        gdal.OF_VECTOR | gdal.OF_READONLY,
    )

    if not input_dataset:
        msg = f"Could not open dataset from {input_dataset}"
        raise FilterError(msg)

    out_driver: ogr.Driver = ogr.GetDriverByName("GPKG")
    output_dataset: ogr.DataSource = out_driver.CreateDataSource(output_path)

    for i in range(0, input_dataset.GetLayerCount()):
        in_layer: ogr.Layer = input_dataset.GetLayerByIndex(i)

        filter_layer(in_layer=in_layer, area=area, output_dataset=output_dataset)

        LOGGER.info(
            f"Layer saved to {output_path}|layername={in_layer.GetName()}",
        )
