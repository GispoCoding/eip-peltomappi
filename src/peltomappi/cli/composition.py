from pathlib import Path
import click

from peltomappi.cli.utils import str_to_path
from peltomappi.composition import Composition


@click.group(help="Commands to manage compositions i.e. a collection of one or more subprojects")
def composition():
    pass


@composition.command(help="Creates a new composition and saves it to a JSON file")
@click.option(
    "--parcelspec",
    "-p",
    multiple=True,
)
@click.argument(
    "output",
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
    "template_project_directory",
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
    "full_data_path",
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
    "subproject_output_directory",
    type=click.Path(
        exists=False,
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.argument(
    "name",
    type=click.STRING,
)
@click.argument(
    "workspace",
    type=click.STRING,
)
@click.option(
    "--server",
    type=click.STRING,
    default="https://app.merginmaps.com",
    help="Specify non-default Mergin Maps Server",
)
def create(
    parcelspec: tuple[Path, ...],
    output: Path,
    template_project_directory: Path,
    full_data_path: Path,
    subproject_output_directory: Path,
    name: str,
    workspace: str,
    server: str,
):
    if len(parcelspec) == 0:
        msg = "at least one parcel specification must be added"
        raise ValueError(msg)

    comp = Composition.from_parcel_specifications(
        [Path(ps) for ps in parcelspec],
        template_project_directory,
        full_data_path,
        subproject_output_directory,
        workspace,
        name,
        server,
    )

    comp.set_path(output)
    comp.save()


@composition.command(help="Uploads all subprojects in the composition to the Mergin Maps server.")
@click.argument(
    "composition",
    type=click.Path(
        exists=True,
        dir_okay=False,
        file_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
def upload(composition: Path):
    comp = Composition.from_json(composition)
    comp.upload_subprojects()
