import click

from peltomappi.cli.utils import str_to_path
from peltomappi.config import convert_config_json_to_gpkg


@click.group(help="Commands to manage configuration files")
def config():
    pass


@config.command(help="Creates a config geopackage from json")
@click.argument(
    "input_json",
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
    "output_gpkg",
    type=click.Path(
        exists=False,
        dir_okay=False,
        file_okay=True,
        writable=True,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.argument(
    "data_gpkg",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.option(
    "-o",
    "--overwrite",
    type=click.BOOL,
    is_flag=True,
    help="Allow command to overwrite files",
)
def convert(
    input_json,
    output_gpkg,
    data_gpkg,
    overwrite,
):
    convert_config_json_to_gpkg(
        input_json,
        output_gpkg,
        data_gpkg,
        overwrite=overwrite,
    )
