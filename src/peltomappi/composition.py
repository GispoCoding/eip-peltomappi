import os
from pathlib import Path
from typing import Any, Self
from uuid import UUID, uuid4

import json
import jsonschema
import mergin


from peltomappi.logger import LOGGER
from peltomappi.parcelspec import ParcelSpecification
from peltomappi.subproject import TEMPLATE_QGIS_PROJECT_NAME, Subproject
from peltomappi.utils import clean_string_to_filename

PELTOMAPPI_CONFIG_LAYER_NAME = "__peltomappi_config"
FIELD_PARCEL_IDENTIFIER_COLUMN = "PERUSLOHKOTUNNUS"
SCHEMA_COMPOSITION = Path(__file__).parent / "composition.schema.json"
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

    if not (template_project_directory / TEMPLATE_QGIS_PROJECT_NAME).exists():
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
    __full_data_path: Path
    __subproject_directory: Path

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
        full_data_path: Path,
        subproject_directory: Path,
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
        self.__full_data_path = full_data_path
        self.__subproject_directory = subproject_directory

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

    def full_data_path(self) -> Path:
        return self.__full_data_path

    def subproject_directory(self) -> Path:
        return self.__subproject_directory

    def to_json_dict(self) -> dict[str, Any]:
        d = {
            "compositionId": str(self.__id),
            "compositionName": self.__name,
            "merginWorkspace": self.__mergin_workspace,
            "merginServer": self.__mergin_server,
            "templateProjectPath": self.__template_project_path.__str__(),
            "subprojects": [subproject.conf_path().__str__() for subproject in self.__subprojects],
            "fullDataPath": self.__full_data_path.__str__(),
            "subprojectDirectory": self.__subproject_directory.__str__(),
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
            Path(data["fullDataPath"]),
            Path(data["subprojectDirectory"]),
        )

    @classmethod
    def from_parcel_specifications(
        cls,
        parcelspec_jsons: list[Path],
        template_project_directory: Path,
        full_data_path: Path,
        subproject_output_directory: Path,
        workspace: str,
        composition_name: str,
        server: str,
    ) -> Self:
        subproject_output_directory.mkdir()
        id = uuid4()
        parcelspecs = [ParcelSpecification.from_json(json_file) for json_file in parcelspec_jsons]

        subprojects = []

        for parcelspec in parcelspecs:
            subproject_dir = subproject_output_directory / clean_string_to_filename(parcelspec.name())
            subproject = parcelspec.to_subproject(
                template_project_directory,
                subproject_dir,
                full_data_path,
                id,
            )

            subprojects.append(subproject)

        return cls(
            id,
            composition_name,
            workspace,
            server,
            template_project_directory,
            subprojects,
            full_data_path,
            subproject_output_directory,
        )

    def add_subproject_from_parcelspec(self, parcelspec_path: Path) -> None:
        # TODO: doesn't have a test and should
        parcelspec = ParcelSpecification.from_json(parcelspec_path)
        subproject = parcelspec.to_subproject(
            self.__template_project_path,
            self.__subproject_directory / clean_string_to_filename(parcelspec.name()),
            self.__full_data_path,
            self.__id,
        )

        subproject.save()

        self.__subprojects.append(subproject)
        self.save()

    def upload_subprojects(self):
        client = mergin.MerginClient(
            login=os.getenv("MERGIN_USERNAME"), password=os.getenv("MERGIN_PASSWORD"), url=self.__mergin_server
        )

        existing_project_names = [proj["name"] for proj in client.projects_list(only_namespace=self.__mergin_workspace)]
        for s in self.__subprojects:
            sp_name = f"{self.__name}_{s.name()}"

            if sp_name in existing_project_names:
                LOGGER.info(f"Project {sp_name} already exists in server, skipping...")
                continue

            s.upload(
                self.__mergin_workspace,
                sp_name,
                client,
            )
