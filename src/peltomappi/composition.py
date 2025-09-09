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
    """
    Backend for how Composition interacts with projects.
    """

    @abstractmethod
    def download_project(self, project_name: str, destination: Path) -> None:
        """
        Downloads project to destination path.
        """
        pass

    @abstractmethod
    def upload_project(self, project_name: str, directory: Path) -> None:
        """
        Uploads project from given directory with the given name.
        """
        pass

    @abstractmethod
    def projects_list(self, workspace: str) -> list[str]:
        """
        Lists existing projects in the backend.
        """
        pass


class MerginBackend(CompositionBackend):
    __client: mergin.MerginClient | None
    __server: str

    def __init__(self, server: str) -> None:
        self.__client = None
        self.__server = server

    def client(self) -> mergin.MerginClient:
        """
        Returns a MerginMaps Server client, initializing if it doesn't already
        exist, fetching the login details from environment variables.

        Returns:
            mergin client

        Raises:
            ClientError: indirectly, if client could not be initialized
        """
        if self.__client is None:
            self.__client = mergin.MerginClient(
                login=os.getenv("MERGIN_USERNAME"),
                password=os.getenv("MERGIN_PASSWORD"),
                url=self.__server,
            )

        return self.__client

    def download_project(self, project_name: str, destination: Path) -> None:
        """
        Downloads project to destination path.
        """
        self.client().download_project(
            project_name,
            destination,
        )

    def upload_project(self, project_name: str, directory: Path) -> None:
        """
        Uploads project from given directory with the given name.
        """
        self.client().create_project_and_push(
            project_name=project_name,
            directory=directory,
            is_public=False,
        )

    def projects_list(self, workspace: str) -> list[str]:
        """
        Lists existing project names in the given workspace.
        """
        return [proj["name"] for proj in self.client().projects_list(only_namespace=workspace)]


class CompositionError(Exception):
    pass


class Composition:
    """
    A composition is a collection of Subprojects which belong to the same
    group. It is stored on disk as a folder, with the following structure:

        <composition-name>
        ├── .composition
        │   ├── composition.json
        │   └── full_data
        │       └── <data-gpkg>
        ├── <subproject-name> (0..N)
        │   ├── peltomappi_subproject.json
        │   └── etc ...
        └── <template-name>
            ├── <data-gpkg>
            └── etc ...

    The composition configuration is saved as a JSON file following a JSON
    schema.

    A composition is meant to be shareable, such that multiple users can
    download the composition and use it.

    The Composition class is used to initialize and manipulate compositions.
    """

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
        """
        Initializes a composition. Not meant to be used directly, use one of
        the class methods instead.
        """
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
        """
        Returns:
            Path to the directory where subprojects and template project exist.
        """
        return (self.__path / "../").resolve()

    def template_project_path(self) -> Path:
        """
        Returns:
            Path to the template project directory.
        """
        return self.projects_path() / clean_string_to_filename(self.__template_name)

    def full_data_path(self) -> Path:
        """
        Returns:
            Path to the directory containing the full data.
        """
        return self.__path / "full_data"

    def subproject_path(self, subproject_name: str) -> Path:
        """
        Returns:
            Path to the subproject with the given name.
        """
        return self.projects_path() / clean_string_to_filename(subproject_name)

    def mergin_name(self) -> str:
        """
        Returns:
            Name of this composition, stripped of anything but alphanumeric symbols and underscores.
        """
        return clean_string_to_filename(self.__name)

    def mergin_name_with_workspace(self) -> str:
        """
        Returns:
            Cleaned name of the composition in the Mergin Maps format
        """
        return f"{self.__mergin_workspace}/{clean_string_to_filename(self.__name)}"

    def subproject_mergin_name_with_workspace(self, subproject_name: str) -> str:
        """
        Returns:
            Cleaned name of the given subproject in the Mergin Maps format
        """
        return f"{self.__mergin_workspace}/{clean_string_to_filename(self.__name)}_{clean_string_to_filename(subproject_name)}"

    def subproject_mergin_name(self, subproject_name: str) -> str:
        """
        Returns:
            Cleaned name of the given subproject
        """
        return f"{clean_string_to_filename(self.__name)}_{clean_string_to_filename(subproject_name)}"

    def template_mergin_name_with_workspace(self) -> str:
        """
        Returns:
            Cleaned name of the template project
        """
        return f"{self.__mergin_workspace}/{self.__template_name}"

    def json_config_path(self) -> Path:
        """
        Returns:
            Path of this composition's JSON configuration file.
        """
        return self.__path / "composition.json"

    def to_json_dict(self) -> dict[str, Any]:
        """
        Returns:
            dictionary which can be saved as a JSON file
        """
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
        """
        Saves this composition to a JSON file.
        """
        with self.json_config_path().open("w") as file:
            json.dump(self.to_json_dict(), file, indent=4)

    def download_template_project(self) -> None:
        """
        Downloads template project to its corresponding directory with the set
        backend.
        """
        self.__backend.download_project(
            self.template_mergin_name_with_workspace(),
            self.template_project_path(),
        )

    def download_subproject(self, subproject_name: str) -> None:
        """
        Downloads subproject of the given name to its corresponding directory
        with the set backend.
        """
        self.__backend.download_project(
            self.subproject_mergin_name_with_workspace(subproject_name),
            self.subproject_path(subproject_name),
        )

    @classmethod
    def initialize(
        cls,
        path: Path,
        template_name: str,
        name: str,
        mergin_workspace: str,
        mergin_server: str,
        backend: CompositionBackend,
    ) -> Self:
        """
        Initializes an empty composition (with no subprojects). Creates the
        folder structure and saves the composition as a JSON configuration
        file.
        """
        composition_path = path / ".composition"
        composition_path.mkdir(parents=True)

        comp = cls(
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

        return comp

    @classmethod
    def from_json(
        cls,
        json_config: Path,
        backend: CompositionBackend,
        *,
        download_subprojects: bool = False,
    ) -> Self:
        """
        Creates a Composition from an existing JSON configuration file.
        """
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
        """
        Adds a subproject to this composition from a parcel specification JSON
        file.
        """
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
        """
        Uploads this composition as a project to the set backend.

        Note:
            This is meant for an initial upload, when the composition does not
            yet exist in the backend. This does nothing to update a modified
            composition.
        """
        self.__backend.upload_project(
            project_name=self.mergin_name_with_workspace(),
            directory=self.__path,
        )

    def upload_subprojects(self) -> None:
        """
        Uploads all subprojects in this composition to the set backend.

        Note:
            This is meant for an initial upload, if the project already exists
            its upload will be skipped.
        """
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
