import tempfile

from pathlib import Path

from peltomappi.config import Config
from peltomappi.divider import Divider
from peltomappi.logger import LOGGER
from peltomappi.utils import clean_string_to_filename


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

    def create_subprojects(self):
        temp_dir = tempfile.TemporaryDirectory()
        temp_dir_path = Path(temp_dir.name)

        for file in self.__input_project.glob("*.gpkg"):
            LOGGER.info(f"DIVIDING {file.stem}")
            divider = Divider(
                input_dataset=file,
                output_dir=temp_dir_path,
                config=self.__config,
                filename=file.stem,
            )
            divider.divide()

        for description in self.__config.descriptions():
            description = clean_string_to_filename(description)
            print(type(description), description)
