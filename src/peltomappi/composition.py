import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from jsonschema import validate

from peltomappi.filter import filter_dataset_by_field_parcel_ids, get_spatial_filter_from_field_parcel_ids
from peltomappi.logger import LOGGER
from peltomappi.utils import config_name_to_path


class CompositionError(Exception):
    pass


PELTOMAPPI_CONFIG_LAYER_NAME = "__peltomappi_config"
FIELD_PARCEL_IDENTIFIER_COLUMN = "PERUSLOHKOTUNNUS"
SCHEMA_SUBPROJECTS = Path(__file__).parent / "subprojects.schema.json"
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


def __create_subprojects(
    subprojects_json: Path,
    template_project_directory: Path,
    full_data_directory: Path,
    output_directory: Path,
    filter_dataset: Path,
    composition_name: str,
    workspace: str,
    server: str,
) -> dict[str, Any]:
    """ """
    validate_template_project(template_project_directory)

    schema = json.loads(SCHEMA_SUBPROJECTS.read_text())
    data = json.loads(subprojects_json.read_text())

    validate(data, schema=schema)

    parcel_specs = data["parcelSpecifications"]

    output_directory.mkdir(parents=True, exist_ok=True)
    full_data_gpkgs: tuple[str, ...] = tuple([gpkg.name for gpkg in full_data_directory.glob("*.gpkg")])

    def __create_subproject(
        full_data_directory: Path,
        output_directory: Path,
        field_parcel_ids: set[str],
        name: str,
    ) -> dict[str, Any]:
        LOGGER.info("Copying project files...")
        subproject_id = str(uuid4())
        for file in template_project_directory.iterdir():
            if (
                file.name.endswith(".gpkg")
                or file.name.endswith(".gpkg-wal")
                or file.name.endswith(".gpkg-shm")
                or file.stem == ".mergin"
                or file.stem == "proj"
            ):
                continue

            if file.stem == TEMPLATE_QGIS_PROJECT_NAME:
                shutil.copy(
                    file,
                    output_directory
                    / f"{TEMPLATE_QGIS_PROJECT_NAME}_{subproject_id}.{TEMPLATE_QGIS_PROJECT_EXTENSION}",
                )
                continue

            if file.is_dir():
                shutil.copytree(file, output_directory / file.stem)
            else:
                shutil.copy(file, output_directory)

        LOGGER.info("Dividing project data...")

        spatial_filter = get_spatial_filter_from_field_parcel_ids(
            filter_dataset,
            field_parcel_ids,
        )

        for file in template_project_directory.glob("*.gpkg"):
            if file.name in full_data_gpkgs:
                continue

            LOGGER.info(f"Dividing {file.stem}...")
            filter_dataset_by_field_parcel_ids(
                file,
                output_directory / f"{file.stem}.gpkg",
                spatial_filter,
            )

        for file in full_data_directory.glob("*.gpkg"):
            LOGGER.info(f"Dividing {file.stem}...")
            filter_dataset_by_field_parcel_ids(
                file,
                output_directory / f"{file.stem}.gpkg",
                spatial_filter,
            )

        LOGGER.info(f"Subproject created at {output_directory}")

        output = {
            "id": subproject_id,
            "name": name,
            "path": str(output_directory),
            "fieldParcelIds": [*field_parcel_ids],
            "created": datetime.now().isoformat(),
        }

        return output

    subprojects = []
    for parcel_spec in parcel_specs:
        name = parcel_spec["name"]
        ids = set(parcel_spec["fieldParcelIds"])
        subproject_dir = config_name_to_path(name, output_directory)
        subproject_dir.mkdir(exist_ok=False)

        subproject = __create_subproject(full_data_directory, subproject_dir, ids, name)

        subprojects.append(subproject)

    return {
        "compositionId": str(uuid4()),
        "compositionName": composition_name,
        "merginWorkspace": workspace,
        "merginServer": server,
        "templateProjectPath": str(template_project_directory),
        "subprojects": subprojects,
    }


def create_from_subprojects_json(
    subprojects_json: Path,
    output: Path,
    template_project_directory: Path,
    full_data_path: Path,
    subproject_output_directory: Path,
    workspace: str,
    composition_name: str,
    server: str,
    *,
    overwrite: bool = False,
):
    if not overwrite and output.exists():
        msg = f"attempting to write file {output} but it already exists and overwrite has not been permitted"
        raise CompositionError(msg)

    filter_dataset = full_data_path / "peltolohkot_2024.gpkg"
    composition = __create_subprojects(
        subprojects_json,
        template_project_directory,
        full_data_path,
        subproject_output_directory,
        filter_dataset,
        composition_name,
        workspace,
        server,
    )

    schema = json.loads(SCHEMA_COMPOSITION.read_text())
    validate(composition, schema=schema)

    with open(output, "w") as file:
        json.dump(composition, file, indent=4)
