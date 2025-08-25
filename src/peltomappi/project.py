from pathlib import Path
import shutil

from peltomappi.config import Config
from peltomappi.divider import Divider
from peltomappi.logger import LOGGER
from peltomappi.utils import clean_string_to_filename


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
        Splits project to subprojects based on set config.

        Raises:
            ProjectError: if directory for a subproject was not correctly created.
        """
        for file in self.__input_project.glob("*.gpkg"):
            LOGGER.info(f"DIVIDING {file.stem}")
            divider = Divider(
                input_dataset=file,
                output_dir=self.__output_directory,
                config=self.__config,
                filename=file.stem,
            )
            divider.divide()

        for description in self.__config.descriptions():
            description = clean_string_to_filename(description)

            # divider should've created this, raise error if for some reason it
            # didn't
            subproject_dir = self.__output_directory / description

            if not subproject_dir.exists():
                msg = f"subproject directory {subproject_dir} was not created!"
                raise ProjectError(msg)

            for file in self.__input_project.iterdir():
                if (
                    file.name.endswith(".gpkg")
                    or file.name.endswith(".gpkg-wal")
                    or file.name.endswith(".gpkg-shm")
                    or file.stem == ".mergin"
                    or file.stem == "proj"
                ):
                    continue

                shutil.copy(file, subproject_dir)
