import json
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, NamedTuple, Self
from uuid import UUID, uuid4

import jsonschema

from peltomappi.filter import filter_dataset_by_field_parcel_ids, get_spatial_filter_from_field_parcel_ids
from peltomappi.logger import LOGGER

SCHEMA_SUBPROJECT = Path(__file__).parent / "subproject.schema.json"
TEMPLATE_QGIS_PROJECT_NAME = "peltomappi.qgs"
TEMPLATE_MERGIN_CONFIG_NAME = "mergin-config.json"
FILTER_DATASET_NAME = "peltolohkot_2024.gpkg"
SUBPROJECT_CONFIG_NAME = "peltomappi_subproject.json"


# TODO: currently there's bit of an awkward situation where this class can represent
# both an invalid, uncreated subproject but also a valid existing subproject.
# probably a better solution would be to have a new class ParcelSpecification or
# similar for the non-created, "preliminary" subproject


class ModificationType(Enum):
    PROJECT_UPDATE = "PROJECT_UPDATE"
    WEATHER_UPDATE = "WEATHER_UPDATE"


class ModificationAction(NamedTuple):
    mod_type: ModificationType
    timestamp: datetime

    def to_json_dict(self) -> dict[str, str]:
        return {
            "modificationType": self.mod_type.value,
            "datetime": self.timestamp.isoformat(),
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict[str, str]) -> Self:
        return cls(
            mod_type=ModificationType[json_dict["modificationType"]],
            timestamp=datetime.fromisoformat(json_dict["datetime"]),
        )


class SubprojectError(Exception):
    pass


class Subproject:
    __id: UUID | None
    __name: str
    __path: Path | None
    __field_parcel_ids: list[str]
    __created: datetime | None
    __modified: list[ModificationAction] | None
    __composition_id: UUID | None

    def __init__(
        self,
        id: UUID | None,
        name: str,
        path: Path | None,
        field_parcel_ids: list[str],
        created: datetime | None,
        modified: list[ModificationAction] | None,
        composition_id: UUID | None,
    ) -> None:
        self.__id = id
        self.__name = name
        self.__path = path
        self.__field_parcel_ids = field_parcel_ids
        self.__created = created
        self.__modified = modified
        self.__composition_id = composition_id

    @classmethod
    def from_json(cls, json_path: Path) -> Self:
        schema = json.loads(SCHEMA_SUBPROJECT.read_text())
        data = json.loads(json_path.read_text())

        jsonschema.validate(data, schema=schema)

        modified_json: list[dict[str, str]] | None = data.get("modified")

        if modified_json:
            modified = [ModificationAction.from_json_dict(d) for d in modified_json]
        else:
            modified = None

        id = None if not data.get("id") else UUID(data["id"])
        path = None if not data.get("path") else Path(data["path"])
        created = None if not data.get("created") else datetime.fromisoformat(data["created"])
        composition_id = None if not data.get("compositionId") else UUID(data["compositionId"])

        return cls(
            id,
            data["name"],
            path,
            data["fieldParcelIds"],
            created,
            modified,
            composition_id,
        )

    def create(
        self,
        template_project_directory: Path,
        output_directory: Path,
        full_data_directory: Path,
        composition_id: UUID,
    ) -> None:
        if any(
            [
                self.__id is not None,
                self.__path is not None,
                self.__created is not None,
                self.__modified is not None,
                self.__composition_id is not None,
            ]
        ):
            msg = "subproject appears to have already been created"
            raise SubprojectError(msg)

        if output_directory.exists():
            msg = "output directory already exists"
            raise SubprojectError(msg)

        output_directory.mkdir()

        filter_dataset = full_data_directory / FILTER_DATASET_NAME
        full_data_gpkgs = tuple([gpkg.name for gpkg in full_data_directory.glob("*.gpkg")])

        LOGGER.info("Copying project files...")
        self.__id = uuid4()
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

        spatial_filter = get_spatial_filter_from_field_parcel_ids(
            filter_dataset,
            set(self.__field_parcel_ids),
        )

        for file in template_project_directory.glob("*.gpkg"):
            if file.name in full_data_gpkgs:
                continue

            LOGGER.info(f"Dividing {file.stem}...")
            filter_dataset_by_field_parcel_ids(
                file,
                output_directory / f"{file.stem}.gpkg",
                spatial_filter,
            )

        for file in full_data_directory.glob("*.gpkg"):
            LOGGER.info(f"Dividing {file.stem}...")
            filter_dataset_by_field_parcel_ids(
                file,
                output_directory / f"{file.stem}.gpkg",
                spatial_filter,
            )

        self.__path = output_directory
        self.__created = datetime.now()
        self.__modified = []
        self.__composition_id = composition_id

        self.save()

        LOGGER.info(f"Subproject created at {output_directory}")

    def id(self) -> UUID | None:
        return self.__id

    def name(self) -> str:
        return self.__name

    def path(self) -> Path | None:
        return self.__path

    def field_parcel_ids(self) -> list[str]:
        return self.__field_parcel_ids

    def created(self) -> datetime | None:
        return self.__created

    def modified(self) -> list[ModificationAction] | None:
        return self.__modified

    def composition_id(self) -> UUID | None:
        return self.__composition_id

    def to_json_dict(self) -> dict[str, Any]:
        if self.__id is None or self.__path is None or self.__created is None or self.__composition_id is None:
            # TODO: don't do this
            msg = "subproject hasn't been created yet"
            raise SubprojectError(msg)

        d: dict[str, Any] = {
            "id": str(self.__id),
            "name": self.__name,
            "path": self.__path.__str__(),
            "fieldParcelIds": self.__field_parcel_ids,
            "compositionId": str(self.__composition_id),
            "created": self.__created.isoformat(),
        }

        if self.__modified:
            modifications = [mod.to_json_dict() for mod in self.__modified]
            d["modified"] = modifications

        schema = json.loads(SCHEMA_SUBPROJECT.read_text())
        jsonschema.validate(d, schema=schema)

        return d

    def save(self) -> None:
        if self.__path is None:
            msg = "path is not set, can't save"
            raise SubprojectError(msg)

        # path is a directory
        output_path = self.__path / SUBPROJECT_CONFIG_NAME

        with output_path.open("w") as file:
            json.dump(self.to_json_dict(), file, indent=4)

    def set_path(self, path: Path):
        self.__path = path
