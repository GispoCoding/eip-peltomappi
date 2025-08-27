from pathlib import Path
import shutil

from peltomappi.config import Config
from peltomappi.divider import Divider
from peltomappi.logger import LOGGER
from peltomappi.utils import config_description_to_path


class ProjectError(Exception):
    pass


class Project:
    """
    Class for dealing with projects.
    """

    __input_project: Path
    __output_directory: Path
    __config: Config

    def __init__(
        self,
        input_project: Path,
        output_directory: Path,
        config: Config,
    ) -> None:
        """
        Sets state for Project.

        Args:
            input_project: path to the input project
            output_dir: directory for any outputs
            config_gpkg: path to a configuration GeoPackage
        """
        self.__input_project = input_project
        self.__output_directory = output_directory
        self.__config = config

    def divide_to_subprojects(self):
        """
        Splits project to subprojects based on set config. Project files are
        not changed and are copied as is, but any background data is divided
        according to the config.

        Raises:
            ProjectError: if directory for a subproject was not correctly created.
        """
        for description, filter_geom in self.__config.to_dict().items():
            subproject_dir = config_description_to_path(description, self.__output_directory)
            subproject_dir.mkdir(exist_ok=True)

            if not subproject_dir.exists():
                msg = f"subproject directory {subproject_dir} was not created!"
                raise ProjectError(msg)

            LOGGER.info("Copying project files...")
            for file in self.__input_project.iterdir():
                if (
                    file.name.endswith(".gpkg")
                    or file.name.endswith(".gpkg-wal")
                    or file.name.endswith(".gpkg-shm")
                    or file.stem == ".mergin"
                    or file.stem == "proj"
                ):
                    continue

                if file.is_dir():
                    shutil.copytree(file, subproject_dir / file.stem)
                else:
                    shutil.copy(file, subproject_dir)

            LOGGER.info("Dividing project data...")
            for file in self.__input_project.glob("*.gpkg"):
                if file.resolve() == self.__config.path().resolve():
                    continue

                LOGGER.info(f"Dividing {file.stem}...")
                Divider.divide_into_area(
                    input_path=file,
                    output_path=subproject_dir / f"{file.stem}.gpkg",
                    area=filter_geom,
                )

            LOGGER.info(f"Subproject created at {subproject_dir}")
