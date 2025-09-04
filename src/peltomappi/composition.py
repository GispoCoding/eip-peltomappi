from pathlib import Path
from typing import Any, Self
from uuid import UUID, uuid4

import json
import jsonschema


from peltomappi.subproject import Subproject
from peltomappi.utils import clean_string_to_filename

PELTOMAPPI_CONFIG_LAYER_NAME = "__peltomappi_config"
FIELD_PARCEL_IDENTIFIER_COLUMN = "PERUSLOHKOTUNNUS"
SCHEMA_COMPOSITION = Path(__file__).parent / "composition.schema.json"
TEMPLATE_QGIS_PROJECT_NAME = "peltomappi"
TEMPLATE_QGIS_PROJECT_EXTENSION = "qgs"
TEMPLATE_MERGIN_CONFIG_NAME = "mergin-config.json"


def validate_template_project(template_project_directory: Path):
    """
    Performs a series of checks on whether the given template project is valid
    for use as a Peltomappi project.

    Raises:
        CompositionError: if any check fails
    """

    if not template_project_directory.exists():
        msg = "project directory does not exist"
        raise CompositionError(msg)

    if not (template_project_directory / f"{TEMPLATE_QGIS_PROJECT_NAME}.{TEMPLATE_QGIS_PROJECT_EXTENSION}").exists():
        msg = "template project does not have a project file"
        raise CompositionError(msg)

    if not (template_project_directory / TEMPLATE_MERGIN_CONFIG_NAME).exists():
        msg = "template project does not have a mergin config file"
        raise CompositionError(msg)


class CompositionError(Exception):
    pass


class Composition:
    __id: UUID
    __name: str
    __mergin_workspace: str
    __mergin_server: str
    __template_project_path: Path
    __subprojects: list[Subproject]

    # not a part of the JSON schema:
    __path: Path | None

    def __init__(
        self,
        id: UUID,
        name: str,
        mergin_workspace: str,
        mergin_server: str,
        template_project_path: Path,
        subprojects: list[Subproject],
        *,
        path: Path | None = None,
    ) -> None:
        self.__id = id
        self.__name = name
        self.__mergin_workspace = mergin_workspace
        self.__mergin_server = mergin_server
        self.__template_project_path = template_project_path
        self.__subprojects = subprojects
        self.__path = path

    def set_id(self, id: UUID) -> None:
        self.__id = id

    def set_mergin_workspace(self, mergin_workspace: str) -> None:
        self.__mergin_workspace = mergin_workspace

    def set_mergin_server(self, mergin_server: str) -> None:
        self.__mergin_server = mergin_server

    def set_name(self, name: str) -> None:
        self.__name = name

    def set_template_project_path(self, template_project_path: Path) -> None:
        self.__template_project_path = template_project_path

    def set_path(self, path: Path) -> None:
        self.__path = path

    def id(self) -> UUID:
        return self.__id

    def name(self) -> str:
        return self.__name

    def mergin_workspace(self) -> str:
        return self.__mergin_workspace

    def mergin_server(self) -> str:
        return self.__mergin_server

    def template_project_path(self) -> Path:
        return self.__template_project_path

    def subprojects(self) -> list[Subproject]:
        return self.__subprojects

    def to_json_dict(self) -> dict[str, Any]:
        d = {
            "compositionId": str(self.__id),
            "compositionName": self.__name,
            "merginWorkspace": self.__mergin_workspace,
            "merginServer": self.__mergin_server,
            "templateProjectPath": self.__template_project_path.name,
            "subprojects": [subproject.path().__str__() for subproject in self.__subprojects],
        }

        schema = json.loads(SCHEMA_COMPOSITION.read_text())
        jsonschema.validate(d, schema=schema)

        return d

    def save(self) -> None:
        if self.__path is None:
            msg = "output path is not set, can't save"
            raise CompositionError(msg)

        with self.__path.open("w") as file:
            json.dump(self.to_json_dict(), file, indent=4)

    @classmethod
    def from_json(cls, json_config: Path) -> Self:
        schema = json.loads(SCHEMA_COMPOSITION.read_text())
        data = json.loads(json_config.read_text())
        jsonschema.validate(data, schema=schema)

        id = UUID(data["compositionId"])

        subprojects = []
        for json_path in data["subprojects"]:
            subproject = Subproject.from_json(Path(json_path))
            if subproject.composition_id() != id:
                msg = "subproject does not belong to this composition"
                raise CompositionError(msg)

            subprojects.append(subproject)

        return cls(
            id,
            data["compositionName"],
            data["merginWorkspace"],
            data["merginServer"],
            Path(data["templateProjectPath"]),
            subprojects,
        )

    @classmethod
    def from_empty_subprojects(
        cls,
        subproject_jsons: list[Path],
        template_project_directory: Path,
        full_data_path: Path,
        subproject_output_directory: Path,
        workspace: str,
        composition_name: str,
        server: str,
    ) -> Self:
        subproject_output_directory.mkdir()
        id = uuid4()
        subprojects = [Subproject.from_json(json_file) for json_file in subproject_jsons]

        for subproject in subprojects:
            subproject_dir = subproject_output_directory / clean_string_to_filename(subproject.name())
            subproject.create(
                template_project_directory,
                subproject_dir,
                full_data_path,
                id,
            )

        return cls(
            id,
            composition_name,
            workspace,
            server,
            template_project_directory,
            subprojects,
        )
