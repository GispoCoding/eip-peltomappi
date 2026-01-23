import re
import pytest

from pathlib import Path
from tempfile import TemporaryDirectory

from peltomappi.exception import InvalidPeltomappiFileError, MissingPeltomappiFileError
from peltomappi.utils import clean_string_to_filename, latest_fulldata_field_parcel_dataset, sha256_file


def test_clean_string_to_filename():
    assert clean_string_to_filename("test") == "test"
    assert clean_string_to_filename("test ") == "test"
    assert clean_string_to_filename("test something") == "testsomething"
    assert clean_string_to_filename("!\"#¤%&/()=?'`´.,|><'") == ""
    assert clean_string_to_filename("test!\"#¤%&/()=?'`´.,|><'") == "test"
    assert clean_string_to_filename("test!\"#¤%&/()=?'`´.,|><'_something") == "test_something"


def test_sha256_file():
    temp_dir = TemporaryDirectory()
    path = Path(temp_dir.name)
    file_path = path / "test"

    with open(file_path, "w") as file:
        file.write("test")

    assert sha256_file(file_path) == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"


def test_latest_fulldata_field_parcel_dataset(test_full_data: Path):
    assert latest_fulldata_field_parcel_dataset(test_full_data) == test_full_data / "Peltolohkot_2024.gpkg"


def test_latest_fulldata_field_parcel_dataset_no_files():
    temp_dir = TemporaryDirectory()
    path = Path(temp_dir.name)
    with pytest.raises(MissingPeltomappiFileError):
        latest_fulldata_field_parcel_dataset(path)


def test_latest_fulldata_field_parcel_dataset_non_gpkg():
    temp_dir = TemporaryDirectory()
    path = Path(temp_dir.name)

    (path / "Peltolohkot_invalid").touch()

    with pytest.raises(
        InvalidPeltomappiFileError,
        match=re.escape("Non-GeoPackage field parcel dataset found."),
    ):
        latest_fulldata_field_parcel_dataset(path)


def test_latest_fulldata_field_parcel_dataset_invalid_name():
    temp_dir = TemporaryDirectory()
    path = Path(temp_dir.name)

    (path / "Peltolohkot_12_12.gpkg").touch()

    with pytest.raises(
        InvalidPeltomappiFileError,
        match=re.escape("Invalid name for field parcel dataset."),
    ):
        latest_fulldata_field_parcel_dataset(path)


def test_latest_fulldata_field_parcel_dataset_no_number():
    temp_dir = TemporaryDirectory()
    path = Path(temp_dir.name)

    (path / "Peltolohkot_aaaa.gpkg").touch()

    with pytest.raises(
        InvalidPeltomappiFileError,
        match=re.escape("Field parcel file does not contain number correctly."),
    ):
        latest_fulldata_field_parcel_dataset(path)
