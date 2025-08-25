import click

from peltomappi.config import Config
from peltomappi.project import Project
from peltomappi.cli.utils import str_to_path


@click.group(help="Commands to manage Peltomappi projects")
def project():
    pass


@project.command(help="Divides an input project into subprojects")
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
def divide(
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
    project.divide_to_subprojects()
