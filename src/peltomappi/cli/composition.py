# from pathlib import Path
# import click
#
# from peltomappi.cli.utils import str_to_path
# from peltomappi.composition import create_from_subprojects_json
#
#
# @click.group(help="Commands to manage compositions i.e. a collection of one or more subprojects")
# def composition():
#     pass
#
#
# @composition.command(help="Creates a new composition and saves it to a JSON file")
# @click.argument(
#     "subprojects_json",
#     type=click.Path(
#         exists=True,
#         dir_okay=False,
#         file_okay=True,
#         readable=True,
#         resolve_path=True,
#     ),
#     callback=str_to_path,
# )
# @click.argument(
#     "output",
#     type=click.Path(
#         exists=False,
#         dir_okay=False,
#         file_okay=True,
#         writable=True,
#         readable=True,
#         resolve_path=True,
#     ),
#     callback=str_to_path,
# )
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
#     "full_data_path",
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
#     "subproject_output_directory",
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
#     "name",
#     type=click.STRING,
# )
# @click.argument(
#     "workspace",
#     type=click.STRING,
# )
# @click.option(
#     "--server",
#     type=click.STRING,
#     default="https://app.merginmaps.com",
#     help="Specify non-default Mergin Maps Server",
# )
# @click.option(
#     "-o",
#     "--overwrite",
#     type=click.BOOL,
#     is_flag=True,
#     help="Allow command to overwrite output JSON file",
# )
# def create(
#     subprojects_json: Path,
#     output: Path,
#     template_project_directory: Path,
#     full_data_path: Path,
#     subproject_output_directory: Path,
#     name: str,
#     workspace: str,
#     server: str,
#     overwrite: bool,
# ):
#     create_from_subprojects_json(
#         subprojects_json,
#         output,
#         template_project_directory,
#         full_data_path,
#         subproject_output_directory,
#         workspace,
#         name,
#         server,
#         overwrite=overwrite,
#     )
