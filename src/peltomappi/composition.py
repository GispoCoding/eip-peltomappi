from abc import ABC, abstractmethod
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
        msg = "template project directory does not exist"
        raise CompositionError(msg)

    if not (template_project_directory / TEMPLATE_QGIS_PROJECT_NAME).exists():
        msg = "template project does not have a project file"
        raise CompositionError(msg)

    if not (template_project_directory / TEMPLATE_MERGIN_CONFIG_NAME).exists():
        msg = "template project does not have a mergin config file"
        raise CompositionError(msg)


class CompositionBackend(ABC):
    @abstractmethod
    def download_project(self, project_name: str, destination: Path) -> None:
        pass

    @abstractmethod
    def upload_project(self, project_name: str, directory: Path) -> None:
        pass

    @abstractmethod
    def projects_list(self, workspace: str) -> list[str]:
        pass


class MerginBackend(CompositionBackend):
    __client: mergin.MerginClient | None
    __server: str

    def __init__(self, server: str) -> None:
        self.__client = None
        self.__server = server

    def client(self) -> mergin.MerginClient:
        if self.__client is None:
            self.__client = mergin.MerginClient(
                login=os.getenv("MERGIN_USERNAME"),
                password=os.getenv("MERGIN_PASSWORD"),
                url=self.__server,
            )

        return self.__client

    def download_project(self, project_name: str, destination: Path) -> None:
        self.client().download_project(
            project_name,
            destination,
        )

    def upload_project(self, project_name: str, directory: Path) -> None:
        self.client().create_project_and_push(
            project_name=project_name,
            directory=directory,
            is_public=False,
        )

    def projects_list(self, workspace: str) -> list[str]:
        return [proj["name"] for proj in self.client().projects_list(only_namespace=workspace)]


class CompositionError(Exception):
    pass


class Composition:
    __id: UUID
    __name: str
    __mergin_workspace: str
    __mergin_server: str
    __template_name: str
    __subprojects: list[Subproject]

    # not a part of the JSON schema:
    __path: Path  # path to the .composition directory
    __backend: CompositionBackend

    def __init__(
        self,
        id: UUID,
        name: str,
        mergin_workspace: str,
        mergin_server: str,
        template_name: str,
        subprojects: list[Subproject],
        path: Path,
        backend: CompositionBackend,
    ) -> None:
        self.__id = id
        self.__name = name
        self.__mergin_workspace = mergin_workspace
        self.__mergin_server = mergin_server
        self.__template_name = template_name
        self.__subprojects = subprojects
        self.__path = path
        self.__backend = backend

    def id(self) -> UUID:
        return self.__id

    def name(self) -> str:
        return self.__name

    def mergin_workspace(self) -> str:
        return self.__mergin_workspace

    def mergin_server(self) -> str:
        return self.__mergin_server

    def template_name(self) -> str:
        return self.__template_name

    def subprojects(self) -> list[Subproject]:
        return self.__subprojects

    def path(self) -> Path:
        return self.__path

    def backend(self) -> CompositionBackend:
        return self.__backend

    def projects_path(self) -> Path:
        return (self.__path / "../").resolve()

    def template_project_path(self) -> Path:
        return self.projects_path() / clean_string_to_filename(self.__template_name)

    def full_data_path(self) -> Path:
        return self.__path / "full_data"

    def subproject_path(self, subproject_name: str) -> Path:
        return self.projects_path() / clean_string_to_filename(subproject_name)

    def mergin_name(self) -> str:
        return clean_string_to_filename(self.__name)

    def mergin_name_with_workspace(self) -> str:
        return f"{self.__mergin_workspace}/{clean_string_to_filename(self.__name)}"

    def subproject_mergin_name_with_workspace(self, subproject_name: str) -> str:
        return f"{self.__mergin_workspace}/{clean_string_to_filename(self.__name)}_{clean_string_to_filename(subproject_name)}"

    def subproject_mergin_name(self, subproject_name: str) -> str:
        return f"{clean_string_to_filename(self.__name)}_{clean_string_to_filename(subproject_name)}"

    def json_config_path(self) -> Path:
        return self.__path / "composition.json"

    def to_json_dict(self) -> dict[str, Any]:
        d = {
            "compositionId": str(self.__id),
            "compositionName": self.__name,
            "merginWorkspace": self.__mergin_workspace,
            "merginServer": self.__mergin_server,
            "templateName": self.__template_name,
            "subprojects": [subproject.name() for subproject in self.__subprojects],
        }

        schema = json.loads(SCHEMA_COMPOSITION.read_text())
        jsonschema.validate(d, schema=schema)

        return d

    def save(self) -> None:
        with self.json_config_path().open("w") as file:
            json.dump(self.to_json_dict(), file, indent=4)

    def mergin_project_path(self, project_name: str) -> str:
        return f"{self.__mergin_workspace}/{project_name}"

    def download_template_project(self) -> None:
        self.__backend.download_project(
            self.mergin_project_path(self.template_name()),
            self.template_project_path(),
        )

    def download_subproject(self, subproject_name: str) -> None:
        self.__backend.download_project(
            self.subproject_mergin_name_with_workspace(subproject_name),
            self.subproject_path(subproject_name),
        )

    @staticmethod
    def initialize(
        path: Path,
        template_name: str,
        name: str,
        mergin_workspace: str,
        mergin_server: str,
        backend: CompositionBackend,
    ) -> None:
        composition_path = path / ".composition"
        composition_path.mkdir(parents=True)

        comp = Composition(
            uuid4(),
            name,
            mergin_workspace,
            mergin_server,
            template_name,
            [],
            composition_path,
            backend,
        )

        comp.full_data_path().mkdir()
        comp.download_template_project()
        validate_template_project(comp.template_project_path())
        comp.save()

    @classmethod
    def from_json(
        cls,
        json_config: Path,
        backend: CompositionBackend,
        *,
        download_subprojects: bool = False,
    ) -> Self:
        schema = json.loads(SCHEMA_COMPOSITION.read_text())
        data = json.loads(json_config.read_text())
        jsonschema.validate(data, schema=schema)

        id = UUID(data["compositionId"])

        subprojects: list[Subproject] = []
        comp = cls(
            id,
            data["compositionName"],
            data["merginWorkspace"],
            data["merginServer"],
            data["templateName"],
            subprojects,
            Path(json_config.parent),
            backend,
        )

        composition_root = (json_config.parent / "../").resolve()
        for subproject_name in data["subprojects"]:
            subproject_config = (
                composition_root / f"{clean_string_to_filename(subproject_name)}/peltomappi_subproject.json"
            )
            if not subproject_config.exists() and download_subprojects:
                comp.download_subproject(subproject_name)

            subproject = Subproject.from_json(subproject_config)
            if subproject.composition_id() != id:
                msg = "subproject does not belong to this composition"
                raise CompositionError(msg)

            subprojects.append(subproject)

        return comp

    def add_subproject_from_parcelspec(self, parcelspec_path: Path) -> None:
        # TODO: doesn't have a test and should
        parcelspec = ParcelSpecification.from_json(parcelspec_path)
        subproject = parcelspec.to_subproject(
            self.template_project_path(),
            self.subproject_path(parcelspec.name()),
            self.full_data_path(),
            self.__id,
        )

        subproject.save()

        self.__subprojects.append(subproject)
        self.save()

    def upload(self) -> None:
        self.__backend.upload_project(
            project_name=self.mergin_name_with_workspace(),
            directory=self.__path,
        )

    def upload_subprojects(self) -> None:
        existing_project_names = self.__backend.projects_list(self.__mergin_workspace)
        for s in self.__subprojects:
            sp_name = self.subproject_mergin_name(s.name())

            if sp_name in existing_project_names:
                LOGGER.info(f"Project {sp_name} already exists in server, skipping...")
                continue

            self.__backend.upload_project(
                self.subproject_mergin_name_with_workspace(s.name()),
                s.path(),
            )
