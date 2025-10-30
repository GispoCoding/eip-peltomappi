import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Self
from uuid import UUID, uuid4

import jsonschema

from peltomappi.filter import (
    copy_gpkg_as_empty,
    filter_gpkg_by_field_parcel_ids,
    spatial_filter,
    get_spatial_filter_from_field_parcel_ids,
)
from peltomappi.logger import LOGGER
from peltomappi.subproject import Subproject

SCHEMA_PARCEL_SPECIFICATION = Path(__file__).parent / "parcelspecification.schema.json"
FIELD_PARCEL_FILE_PREFIX = "Peltolohkot_"
FILTER_DATASET_NAME = f"{FIELD_PARCEL_FILE_PREFIX}2024.gpkg"


class ParcelSpecificationError(Exception):
    pass


class ParcelSpecification:
    """
    A parcel specification is a simple JSON file which has a JSON schema. It
    contains a name of the specification and the field parcel IDs belonging to
    the it.

    The purpose of the specification is to be turned into a Subproject and
    added to a Composition.
    """

    __name: str
    __field_parcel_ids: list[str]

    def __init__(
        self,
        name: str,
        field_parcel_ids: list[str],
    ) -> None:
        """
        Initializes a subproject. Not meant to be used directly, use one of
        the class methods instead.
        """
        self.__name = name
        self.__field_parcel_ids = field_parcel_ids

    @classmethod
    def from_json(cls, json_path: Path) -> Self:
        """
        Creates a ParcelSpecification from an existing JSON configuration file.
        """
        schema = json.loads(SCHEMA_PARCEL_SPECIFICATION.read_text())
        data = json.loads(json_path.read_text())

        jsonschema.validate(data, schema=schema)

        return cls(
            data["name"],
            data["fieldParcelIds"],
        )

    def to_subproject(
        self,
        template_project_directory: Path,
        output_directory: Path,
        full_data_directory: Path,
        composition_id: UUID,
    ) -> Subproject:
        """
        Turns this parcel specification into a subproject, creating the
        subproject folder and filtering the data from the given full data
        directory.
        """
        if output_directory.exists():
            msg = "output directory already exists"
            raise ParcelSpecificationError(msg)

        output_directory.mkdir()

        filter_dataset = full_data_directory / FILTER_DATASET_NAME
        full_data_gpkgs = tuple([gpkg.name for gpkg in full_data_directory.glob("*.gpkg")])

        LOGGER.info("Copying project files...")
        for file in template_project_directory.iterdir():
            if (
                file.name.endswith(".gpkg")
                or file.name.endswith(".gpkg-wal")
                or file.name.endswith(".gpkg-shm")
                or file.stem == ".mergin"
                or file.stem == "proj"
            ):
                continue

            if file.is_dir():
                shutil.copytree(file, output_directory / file.stem)
            else:
                shutil.copy(file, output_directory)

        LOGGER.info("Dividing project data...")

        spatial_filter_geom = get_spatial_filter_from_field_parcel_ids(
            filter_dataset,
            set(self.__field_parcel_ids),
        )

        for file in template_project_directory.glob("*.gpkg"):
            if file.name in full_data_gpkgs:
                continue

            copy_gpkg_as_empty(file, output_directory / f"{file.stem}.gpkg")

        for file in full_data_directory.glob("*.gpkg"):
            LOGGER.info(f"Dividing {file.stem}...")
            output = output_directory / f"{file.stem}.gpkg"
            if file.stem.startswith(FIELD_PARCEL_FILE_PREFIX):
                filter_gpkg_by_field_parcel_ids(
                    file,
                    output,
                    self.__field_parcel_ids,
                )
            else:
                spatial_filter(
                    file,
                    output,
                    spatial_filter_geom,
                )

        subproject = Subproject(
            uuid4(),
            self.__name,
            self.__field_parcel_ids,
            datetime.now(),
            [],
            composition_id,
            output_directory,
        )

        subproject.save()

        LOGGER.info(f"Subproject created at {output_directory}")

        return subproject

    def name(self) -> str:
        return self.__name

    def field_parcel_ids(self) -> list[str]:
        return self.__field_parcel_ids
