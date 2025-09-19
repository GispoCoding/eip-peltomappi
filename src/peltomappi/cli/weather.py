# import click
#
# from peltomappi.cli.utils import str_to_path
# from peltomappi.config import Config
# from peltomappi.weather import FMIBackend, Weather
#
#
# @click.group(help="Commands to manage weather data")
# def weather():
#     pass
#
#
# @weather.command(help="Writes weather data to projects")
# @click.argument(
#     "output_directory",
#     type=click.Path(
#         exists=True,
#         dir_okay=True,
#         file_okay=False,
#         readable=True,
#         writable=True,
#         resolve_path=True,
#     ),
#     callback=str_to_path,
# )
# @click.argument(
#     "config_gpkg",
#     type=click.Path(
#         exists=True,
#         dir_okay=False,
#         file_okay=True,
#         readable=True,
#         resolve_path=True,
#     ),
#     callback=str_to_path,
# )
# @click.option(
#     "-o",
#     "--overwrite",
#     type=click.BOOL,
#     is_flag=True,
#     help="Allow command to overwrite files",
# )
# def write(
#     output_directory,
#     config_gpkg,
#     overwrite,
# ):
#     config = Config(config_gpkg)
#
#     weather = Weather(
#         config=config,
#         output_dir=output_directory,
#         # FIXME: replace, obviously
#         backend=FMIBackend(),
#         overwrite=overwrite,
#     )
#     weather.write()
