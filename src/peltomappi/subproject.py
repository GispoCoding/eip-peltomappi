import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, NamedTuple, Self
from uuid import UUID

import jsonschema


SCHEMA_SUBPROJECT = Path(__file__).parent / "subproject.schema.json"
TEMPLATE_QGIS_PROJECT_NAME = "peltomappi.qgs"
TEMPLATE_MERGIN_CONFIG_NAME = "mergin-config.json"
SUBPROJECT_CONFIG_NAME = "peltomappi_subproject.json"


class ModificationType(Enum):
    PROJECT_UPDATE = "PROJECT_UPDATE"
    WEATHER_UPDATE = "WEATHER_UPDATE"


class ModificationAction(NamedTuple):
    """
    Specifies when and what type of modification occured. Corresponds to the
    subproject JSON schema.
    """

    mod_type: ModificationType
    timestamp: datetime

    def to_json_dict(self) -> dict[str, str]:
        """
        Returns:
            dictionary which can be saved as a JSON file
        """
        return {
            "modificationType": self.mod_type.value,
            "datetime": self.timestamp.isoformat(),
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict[str, str]) -> Self:
        """
        Creates ModificationAction from a dictionary created from a JSON file.
        """
        return cls(
            mod_type=ModificationType[json_dict["modificationType"]],
            timestamp=datetime.fromisoformat(json_dict["datetime"]),
        )


class SubprojectError(Exception):
    pass


class Subproject:
    """
    A subproject is a folder containing a MerginMaps / QGIS project and its
    data. A subproject belongs to a composition, and should be modified through
    its composition, NOT directly in order to ensure consistency across the
    composition.

    A subproject has its own configuration JSON schema which is stored in the
    subproject folder.

    A subproject is based on a template project, which is defined by the
    composition. Data in the subproject is reduced from the composition's full
    data and filtered according to the field parcel IDs of the subproject.

    A subproject can be created from a parcel specification.
    """

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
        """
        Initializes a subproject. Not meant to be used directly, use one of
        the class methods instead.
        """
        self.__id = id
        self.__name = name
        self.__field_parcel_ids = field_parcel_ids
        self.__created = created
        self.__modified = modified
        self.__composition_id = composition_id
        self.__path = path

    @classmethod
    def from_json(cls, json_path: Path) -> Self:
        """
        Creates a Subproject from an existing JSON configuration file.
        """
        schema = json.loads(SCHEMA_SUBPROJECT.read_text())
        data = json.loads(json_path.read_text())

        jsonschema.validate(data, schema=schema)

        modified_json: list[dict[str, str]] | None = data.get("modified")

        if modified_json:
            modified = [ModificationAction.from_json_dict(d) for d in modified_json]
        else:
            modified = []

        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            field_parcel_ids=data["fieldParcelIds"],
            created=datetime.fromisoformat(data["created"]),
            modified=modified,
            composition_id=UUID(data["compositionId"]),
            path=json_path.parent,
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
        """
        Returns:
            dictionary which can be saved as a JSON file
        """
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
        """
        Saves this subproject to a JSON file.
        """
        with self.json_config_path().open("w") as file:
            json.dump(self.to_json_dict(), file, indent=4)

    def json_config_path(self) -> Path:
        """
        Returns:
            Path of this composition's JSON configuration file.
        """
        return self.__path / SUBPROJECT_CONFIG_NAME

    def add_modified(self, mod: ModificationType, timestamp: datetime) -> None:
        """
        Adds a modified event to this subproject.
        """
        self.__modified.append(
            ModificationAction(
                mod_type=mod,
                timestamp=timestamp,
            )
        )

    def describe(self, *, indent: int = 0) -> None:
        """
        Logs information about this subproject.
        """
        indent_str = "\t" * indent

        def iprint(text: str) -> None:
            print(f"{indent_str}{text}")

        iprint(f'Subproject "{self.__name}" ({self.__id}):')
        iprint(f'\tPath: "{self.__path}"')
        iprint(f'\tPart of composition: "{self.__composition_id}"')
        iprint("\tField Parcel IDs:")
        for id in self.__field_parcel_ids:
            iprint(f"\t\t{id}")
        iprint(f'\tCreated at: "{self.__created}"')
        for mod in self.__modified:
            iprint(f'\tModified at: "{mod.timestamp}", type: "{mod.mod_type}"')
