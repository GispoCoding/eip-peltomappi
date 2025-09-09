import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, NamedTuple, Self
from uuid import UUID

import jsonschema

from peltomappi.logger import LOGGER

SCHEMA_SUBPROJECT = Path(__file__).parent / "subproject.schema.json"
TEMPLATE_QGIS_PROJECT_NAME = "peltomappi.qgs"
TEMPLATE_MERGIN_CONFIG_NAME = "mergin-config.json"
SUBPROJECT_CONFIG_NAME = "peltomappi_subproject.json"


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
    __id: UUID
    __name: str
    __field_parcel_ids: list[str]
    __created: datetime
    __modified: list[ModificationAction]
    __composition_id: UUID

    # not part of the JSON schema
    __path: Path

    def __init__(
        self,
        id: UUID,
        name: str,
        field_parcel_ids: list[str],
        created: datetime,
        modified: list[ModificationAction],
        composition_id: UUID,
        path: Path,
    ) -> None:
        self.__id = id
        self.__name = name
        self.__field_parcel_ids = field_parcel_ids
        self.__created = created
        self.__modified = modified
        self.__composition_id = composition_id
        self.__path = path

    @classmethod
    def from_json(cls, json_path: Path) -> Self:
        schema = json.loads(SCHEMA_SUBPROJECT.read_text())
        data = json.loads(json_path.read_text())

        jsonschema.validate(data, schema=schema)

        modified_json: list[dict[str, str]] | None = data.get("modified")

        if modified_json:
            modified = [ModificationAction.from_json_dict(d) for d in modified_json]
        else:
            modified = []

        return cls(
            UUID(data["id"]),
            data["name"],
            data["fieldParcelIds"],
            datetime.fromisoformat(data["created"]),
            modified,
            UUID(data["compositionId"]),
            json_path.parent,
        )

    def id(self) -> UUID:
        return self.__id

    def name(self) -> str:
        return self.__name

    def path(self) -> Path:
        return self.__path

    def field_parcel_ids(self) -> list[str]:
        return self.__field_parcel_ids

    def created(self) -> datetime:
        return self.__created

    def modified(self) -> list[ModificationAction]:
        return self.__modified

    def composition_id(self) -> UUID:
        return self.__composition_id

    def to_json_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": str(self.__id),
            "name": self.__name,
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
        with self.conf_path().open("w") as file:
            json.dump(self.to_json_dict(), file, indent=4)

    def set_path(self, path: Path):
        LOGGER.warning(
            "set_path() function exists as a way to do dependency injection in tests. Avoid using it in application code."
        )
        self.__path = path

    def conf_path(self) -> Path:
        return self.__path / SUBPROJECT_CONFIG_NAME
