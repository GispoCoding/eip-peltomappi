from pathlib import Path

import tempfile

from osgeo import gdal, ogr

from peltomappi.config import Config
from peltomappi.divider import Divider
from peltomappi.prefix import field_parcel


def test_divider(
    field_parcel_mock_uri: Path,
    field_parcel_config: Path,
):
    temp_dir = tempfile.TemporaryDirectory()
    temp_dir_path = Path(temp_dir.name)

    config = Config(field_parcel_config)

    divider = Divider(
        input_dataset=field_parcel_mock_uri,
        output_dir=temp_dir_path,
        config=config,
        filename_prefix="peltolohkot",
        layer_name_callback=field_parcel,
    )
    divider.divide()

    output_1 = temp_dir_path / "peltolohkot_area1.gpkg"
    output_2 = temp_dir_path / "peltolohkot_area2.gpkg"

    assert output_1.exists()
    assert output_2.exists()

    def test_dataset(
        dataset: gdal.Dataset,
        expected_geom: str,
        expected_values: dict[str, str],
    ):
        assert dataset is not None
        assert dataset.GetLayerCount() == 5

        layer_1: ogr.Layer = dataset.GetLayerByIndex(0)
        layer_2: ogr.Layer = dataset.GetLayerByIndex(1)
        layer_3: ogr.Layer = dataset.GetLayerByIndex(2)
        layer_4: ogr.Layer = dataset.GetLayerByIndex(3)
        layer_5: ogr.Layer = dataset.GetLayerByIndex(4)

        assert layer_1.GetName() == "peltolohko_2024"
        assert layer_2.GetName() == "peltolohko_2023"
        assert layer_3.GetName() == "peltolohko_2022"
        assert layer_4.GetName() == "peltolohko_2021"
        assert layer_5.GetName() == "peltolohko_2020"

        assert layer_1.GetFeatureCount() == 1
        assert layer_2.GetFeatureCount() == 1
        assert layer_3.GetFeatureCount() == 1
        assert layer_4.GetFeatureCount() == 1
        assert layer_5.GetFeatureCount() == 1

        feature_1: ogr.Feature = layer_1.GetFeature(1)
        feature_2: ogr.Feature = layer_2.GetFeature(1)
        feature_3: ogr.Feature = layer_3.GetFeature(1)
        feature_4: ogr.Feature = layer_4.GetFeature(1)
        feature_5: ogr.Feature = layer_5.GetFeature(1)

        assert feature_1.GetGeometryRef().ExportToWkt() == expected_geom
        assert feature_2.GetGeometryRef().ExportToWkt() == expected_geom
        assert feature_3.GetGeometryRef().ExportToWkt() == expected_geom
        assert feature_4.GetGeometryRef().ExportToWkt() == expected_geom
        assert feature_5.GetGeometryRef().ExportToWkt() == expected_geom

        for field, expected_value in expected_values.items():
            value = feature_1.GetFieldAsString(field)
            assert value == expected_value
            value = feature_2.GetFieldAsString(field)
            assert value == expected_value
            value = feature_3.GetFieldAsString(field)
            assert value == expected_value
            value = feature_4.GetFieldAsString(field)
            assert value == expected_value
            value = feature_5.GetFieldAsString(field)
            assert value == expected_value

    expected_geom_1 = "POLYGON ((0 0,1 0,1 1,0 1,0 0))"
    expected_values_1 = {
        "tunnus": "1",
        "vuosi": "2024",
        "peruslohkotunnus": "10",
        "lohkonumero": "10",
        "pinta_ala": "10",
        "kasvikoodi": "1",
        "kasvikoodi_selite_fi": "selite_fi",
        "kasvikoodi_selite_sv": "selite_sv",
        "luomuviljely": "1",
        "virkistyspvm": "1970/01/01",
        "gml_id": "1da2f0ee-b521-4fea-93d7-2ebbf7cc59ea",
    }

    dataset_1: gdal.Dataset = gdal.OpenEx(
        output_1,
        gdal.OF_VECTOR | gdal.OF_READONLY,
    )

    test_dataset(dataset_1, expected_geom_1, expected_values_1)

    expected_geom_2 = "POLYGON ((5 5,6 5,6 4,5 4,5 5))"
    expected_values_2 = {
        "tunnus": "2",
        "vuosi": "2024",
        "peruslohkotunnus": "151",
        "lohkonumero": "123",
        "pinta_ala": "1",
        "kasvikoodi": "kk",
        "kasvikoodi_selite_fi": "",
        "kasvikoodi_selite_sv": "",
        "luomuviljely": "",
        "virkistyspvm": "",
        "gml_id": "a0ce2cf6-389e-4005-890f-5f3d3b33b22a",
    }

    dataset_2: gdal.Dataset = gdal.OpenEx(
        output_2,
        gdal.OF_VECTOR | gdal.OF_READONLY,
    )

    test_dataset(dataset_2, expected_geom_2, expected_values_2)
