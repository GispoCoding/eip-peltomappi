import click
from peltomappi.config import Config
from peltomappi.divider import Divider
from peltomappi.utils import clean_string_to_filename
from peltomappi.cli.utils import str_to_path, prefixtype_to_callback, PrefixType


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
