#!/usr/bin/env python3

import logging
import pathlib
from typing import Callable

import click

from peltomappi.config import Config
from peltomappi.divider import Divider
from peltomappi.logger import LOGGER
from peltomappi.prefix import PrefixType
from peltomappi.project import Project
from peltomappi.utils import clean_string_to_filename


@click.group(help="CLI tool to run Peltomappi processes")
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Only print out errors.",
)
def cli(quiet):
    if quiet:
        LOGGER.setLevel(logging.ERROR)


@click.group(help="Commands to manage Peltomappi projects")
def project():
    pass


def str_to_path(_, __, argument) -> pathlib.Path:
    return pathlib.Path(argument)


def validate_remove_field(_, __, argument) -> tuple[str] | None:
    if len(set(argument)) != len(argument):
        raise click.BadParameter(argument)

    return argument


def prefixtype_to_callback(_, __, argument) -> Callable[[str], str] | None:
    if argument is None:
        return None

    # PrefixType should store functions in a 1-long tuple,
    # retrieve the function by accessing the enum by the user-given
    # string and getting the actual function from the first index
    # of the matching enum value
    return PrefixType[argument].value[0]


@click.command(help="Divides input data into smaller areas, according to a configuration GeoPackage")
@click.argument(
    "input",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.argument(
    "output_directory",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.argument(
    "config_gpkg",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.argument(
    "file_prefix",
    type=click.STRING,
    callback=lambda _, __, x: clean_string_to_filename(x),
)
@click.option(
    "-n",
    "--layer-name-generator",
    type=PrefixType.to_choice(),
    callback=prefixtype_to_callback,
    help="Choose a layer name generator from a list of options",
)
@click.option(
    "-o",
    "--overwrite",
    type=click.BOOL,
    is_flag=True,
    help="Allow command to overwrite files",
)
def divide(
    input,
    output_directory,
    config_gpkg,
    file_prefix,
    layer_name_generator,
    overwrite,
):
    config = Config(config_gpkg)

    divider = Divider(
        input_dataset=input,
        output_dir=output_directory,
        config=config,
        filename=file_prefix,
        layer_name_callback=layer_name_generator,
        overwrite=overwrite,
    )
    divider.divide()


@project.command(help="Creates a new Peltomappi project")
@click.argument(
    "input_directory",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.argument(
    "output_directory",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.argument(
    "config_gpkg",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
def create(
    input_directory,
    output_directory,
    config_gpkg,
):
    config = Config(config_gpkg)

    project = Project(
        input_directory,
        output_directory,
        config,
    )
    project.create_subprojects()


if __name__ == "__main__":
    cli.add_command(divide)
    cli.add_command(project)

    cli()
