from pathlib import Path
import shutil

from peltomappi.config import Config
from peltomappi.filter import filter_dataset
from peltomappi.logger import LOGGER
from peltomappi.utils import config_description_to_path

QGIS_PROJECT_NAME = "peltomappi.qgs"
MERGIN_CONFIG_NAME = "mergin-config.json"


class ProjectError(Exception):
    pass


def validate_template_project(template_project_directory: Path):
    """
    Performs a series of checks on whether the given template project is valid
    for use as a Peltomappi project.

    Raises:
        ProjectError: if any check fails

    """

    if not template_project_directory.exists():
        msg = "project directory does not exist"
        raise ProjectError(msg)

    if not (template_project_directory / QGIS_PROJECT_NAME).exists():
        msg = "template project does not have a project file"
        raise ProjectError(msg)

    if not (template_project_directory / MERGIN_CONFIG_NAME).exists():
        msg = "template project does not have a mergin config file"
        raise ProjectError(msg)


def split_to_subprojects(
    *,
    template_project_directory: Path,
    output_directory: Path,
    config: Config,
):
    """
    Splits project to subprojects based on set config. Project files are
    not changed and are copied as is, but any background data is split
    according to the config.

    Raises:
        ProjectError: if directory for a subproject was not correctly created.
    """
    validate_template_project(template_project_directory)

    for description, filter_geom in config.to_dict().items():
        subproject_dir = config_description_to_path(description, output_directory)
        subproject_dir.mkdir(exist_ok=True)

        if not subproject_dir.exists():
            msg = f"subproject directory {subproject_dir} was not created!"
            raise ProjectError(msg)

        LOGGER.info("Copying project files...")
        for file in template_project_directory.iterdir():
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
        for file in template_project_directory.glob("*.gpkg"):
            LOGGER.info(f"Dividing {file.stem}...")
            filter_dataset(
                input_path=file,
                output_path=subproject_dir / f"{file.stem}.gpkg",
                area=filter_geom,
            )

        LOGGER.info(f"Subproject created at {subproject_dir}")
