from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import shutil
from typing import Any, Self
from uuid import UUID, uuid4

import json
import jsonschema
import keyring
import mergin


from peltomappi.filter import get_spatial_filter_from_field_parcel_ids
from peltomappi.logger import LOGGER
from peltomappi.parcelspec import ParcelSpecification
from peltomappi.subproject import TEMPLATE_QGIS_PROJECT_NAME, ModificationType, Subproject
from peltomappi.utils import clean_string_to_filename, latest_fulldata_field_parcel_dataset, sha256_file
from peltomappi.weather import WeatherBackendTest

FIELD_PARCEL_IDENTIFIER_COLUMN = "peruslohkotunnus"
SCHEMA_COMPOSITION = Path(__file__).parent / "composition.schema.json"
TEMPLATE_MERGIN_CONFIG_NAME = "mergin-config.json"


class CompositionError(Exception):
    pass


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

    @abstractmethod
    def upload_project(self, project_name: str, directory: Path) -> None:
        """
        Uploads project from given directory with the given name.
        """

    @abstractmethod
    def projects_list(self, workspace: str) -> list[str]:
        """
        Lists existing projects in the backend.
        """

    @abstractmethod
    def pull_project(self, directory: Path) -> Any:
        """
        Pulls any changes from the backend to a local directory.
        """

    @abstractmethod
    def push_project(self, directory: Path) -> Any:
        """
        Pushes any changes from the local directory to the backend.
        """


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
            token = keyring.get_password("system", "peltomappi_cli_authentication_token")

            if token is None:
                msg = "token not found! have you logged in?"
                raise CompositionError(msg)

            try:
                self.__client = mergin.MerginClient(
                    auth_token=token,
                    url=self.__server,
                )
            except mergin.ClientError:
                msg = "could not create mergin client, likely invalid token. have you logged in?"
                raise CompositionError(msg)

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

    def pull_project(self, directory: Path) -> Any:
        """
        Pulls any changes from the backend to a local directory.
        """
        return self.client().pull_project(directory)

    def push_project(self, directory: Path) -> Any:
        self.client().push_project(directory)


class Composition:
    """
    A composition is a collection of Subprojects which belong to the same
    group. It is stored on disk as a folder, with the following structure:

        <folder>
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
        backend: CompositionBackend | None = None,
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
        if backend is not None:
            self.__backend = backend
        else:
            self.__backend = MerginBackend(self.__mergin_server)

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

    @staticmethod
    def clone(path: Path, name: str, workspace: str, backend: CompositionBackend) -> None:
        """
        Clones i.e. downloads the composition from the backend with its
        template project and all subprojects.
        """
        path.mkdir()
        composition_path = path / ".composition"

        backend.download_project(f"{workspace}/{name}", composition_path)

        composition_config_path = composition_path / "composition.json"

        Composition.from_json(
            composition_config_path,
            backend=backend,
            download_subprojects=True,
        ).download_template_project()

    @classmethod
    def from_json(
        cls,
        json_config: Path,
        *,
        backend: CompositionBackend | None = None,
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

    def pull(self) -> None:
        """
        Pulls any changes from the backend to the local composition.
        """
        # TODO: conflicts
        LOGGER.info("Pulling composition")
        if conflicts := self.__backend.pull_project(self.__path):
            LOGGER.warning(f"Composition conflicts: {conflicts}")

        LOGGER.info("Pulling template project")
        if conflicts := self.__backend.pull_project(self.template_project_path()):
            LOGGER.warning(f"Template project conflicts: {conflicts}")

        for sp in self.__subprojects:
            LOGGER.info(f'Pulling subproject "{sp.name()}"')

            if conflicts := self.__backend.pull_project(sp.path()):
                LOGGER.warning(f'Subproject "{sp.name()}" conflicts: {conflicts}"')

    def push(self) -> None:
        """
        Pushes local changes from the local composition to the backend. If a
        subproject or the composition does not yet exist in the backend, it
        will be created as a project and uploaded there.
        """
        LOGGER.info("Pushing composition")

        existing_project_names = self.__backend.projects_list(self.__mergin_workspace)
        LOGGER.info("Pushing template project")
        self.__backend.push_project(self.template_project_path())

        for sp in self.__subprojects:
            sp_name = self.subproject_mergin_name(sp.name())

            if sp_name not in existing_project_names:
                LOGGER.info(f'Uploading subproject "{sp.name()}"')
                self.__backend.upload_project(
                    self.subproject_mergin_name_with_workspace(sp.name()),
                    sp.path(),
                )
                continue

            LOGGER.info(f'Pushing subproject "{sp.name()}"')
            self.__backend.push_project(sp.path())

        if self.name() not in existing_project_names:
            LOGGER.info(f'Uploading composition "{self.name()}"')
            self.__backend.upload_project(
                project_name=self.mergin_name_with_workspace(),
                directory=self.__path,
            )
        else:
            LOGGER.info(f'Pushing composition "{self.name()}"')
            self.__backend.push_project(
                self.path(),
            )

    def subprojects_export_csv(self) -> None:
        """
        Exports user data in subprojects to CSV files.
        """
        LOGGER.info("Exporting projects to csv")
        full_data_gpkgs = tuple([gpkg.name for gpkg in self.full_data_path().glob("*.gpkg")])

        for sp in self.__subprojects:
            sp.export_user_data_to_csv(full_data_gpkgs)

    def subprojects_update_weather(self) -> None:
        """
        Updates weather data of each subproject.
        """
        LOGGER.info("Updating weather data")
        backend = WeatherBackendTest()

        filter_dataset = latest_fulldata_field_parcel_dataset(self.full_data_path())
        for sp in self.__subprojects:
            spatial_filter = get_spatial_filter_from_field_parcel_ids(
                filter_dataset,
                set(sp.field_parcel_ids()),
            )

            backend.write_data(
                spatial_filter,
                Path("/tmp"),  # FIXME: remove
                datetime.fromtimestamp(0),
                datetime.fromtimestamp(1),
            )

    def describe(self, *, describe_subprojects: bool = True) -> None:
        print(f'Composition "{self.__name}" ({self.__id}):')
        print(f'\tMergin Server: "{self.__mergin_server}"')
        print(f'\tMergin Workspace: "{self.__mergin_workspace}"')
        print(f'\tTemplate Project: "{self.__template_name}"')
        print(f'\tTemplate Project Folder: "{self.template_project_path()}"')
        print(f'\tTemplate Project with Workspace: "{self.template_mergin_name_with_workspace()}"')
        print(f'\tSubprojects Folder: "{self.projects_path()}"')
        print(f'\tFull Data Folder: "{self.full_data_path()}"')
        print(f'\tMergin Project Name: "{self.mergin_name()}"')
        print(f'\tMergin Project with Workspace: "{self.mergin_name_with_workspace()}"')

        if not describe_subprojects:
            return

        for sp in self.__subprojects:
            sp.describe(indent=1)

    def subprojects_match_template(self) -> None:
        """
        Updates the project files of every subproject in this composition to
        match the template project.

        Note:
            This is meant for updates to the project files. If new data files
            are added, they will not be included.

        Todo:
            Handle data and other files.
        """
        # TODO:
        template_project_path = self.template_project_path() / TEMPLATE_QGIS_PROJECT_NAME
        template_mergin_conf_path = self.template_project_path() / TEMPLATE_MERGIN_CONFIG_NAME

        for sp in self.__subprojects:
            sp_project_path = sp.path() / TEMPLATE_QGIS_PROJECT_NAME
            sp_mergin_conf_path = sp.path() / TEMPLATE_MERGIN_CONFIG_NAME

            if sha256_file(template_project_path) == sha256_file(sp_project_path) and sha256_file(
                template_mergin_conf_path
            ) == sha256_file(sp_mergin_conf_path):
                msg = "no changes in project configuration files"
                raise CompositionError(msg)

            files = [file.name for file in sp.path().iterdir()]

            # Copy new files
            for file in self.template_project_path().iterdir():
                if file.name not in files:
                    if file.is_dir():
                        shutil.copytree(file, sp.path() / file.name)
                        continue

                    shutil.copy(file, sp.path() / file.name)

            shutil.copy(template_project_path, sp_project_path)
            shutil.copy(template_mergin_conf_path, sp_mergin_conf_path)

            sp.add_modified(ModificationType.PROJECT_UPDATE, datetime.now())
            sp.save()

        self.save()
