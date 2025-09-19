# import click
#
# from peltomappi.config import Config
# from peltomappi.cli.utils import str_to_path
# from peltomappi.project import split_to_subprojects
#
#
# @click.group(help="Commands to manage Peltomappi projects")
# def project():
#     pass
#
#
# @project.command(help="Splits an input project into subprojects")
# @click.argument(
#     "template_project_directory",
#     type=click.Path(
#         exists=True,
#         dir_okay=True,
#         file_okay=False,
#         readable=True,
#         resolve_path=True,
#     ),
#     callback=str_to_path,
# )
# @click.argument(
#     "full_data_directory",
#     type=click.Path(
#         exists=True,
#         dir_okay=True,
#         file_okay=False,
#         readable=True,
#         resolve_path=True,
#     ),
#     callback=str_to_path,
# )
# @click.argument(
#     "output_directory",
#     type=click.Path(
#         exists=False,
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
# def split(
#     template_project_directory,
#     full_data_directory,
#     output_directory,
#     config_gpkg,
# ):
#     config = Config(config_gpkg)
#
#     split_to_subprojects(
#         template_project_directory=template_project_directory,
#         full_data_directory=full_data_directory,
#         output_directory=output_directory,
#         config=config,
#     )
