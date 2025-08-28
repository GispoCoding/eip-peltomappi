from pathlib import Path
import shutil

from peltomappi.config import Config
from peltomappi.filter import filter_dataset
from peltomappi.logger import LOGGER
from peltomappi.utils import config_description_to_path


class ProjectError(Exception):
    pass


def split_to_subprojects(
    *,
    template_project_directory: Path,
    output_directory: Path,
    config: Config,
):
    """
    Splits project to subprojects based on set config. Project files are
    not changed and are copied as is, but any background data is spli
    according to the config.

    Raises:
        ProjectError: if directory for a subproject was not correctly created.
    """
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
            if file.resolve() == config.path().resolve():
                continue

            LOGGER.info(f"Dividing {file.stem}...")
            filter_dataset(
                input_path=file,
                output_path=subproject_dir / f"{file.stem}.gpkg",
                area=filter_geom,
            )

        LOGGER.info(f"Subproject created at {subproject_dir}")


def upload_project(project_directory: Path):
    print(f"uploading {project_directory}, supposedly")
