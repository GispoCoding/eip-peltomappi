import os
from pathlib import Path
import click
import mergin

from peltomappi.cli.utils import resolve_composition_input, str_to_path
from peltomappi.composition import Composition, MerginBackend


DEFAULT_MERGIN_SERVER = "http://localhost:8080"


def mergin_backend(server: str) -> MerginBackend:
    return MerginBackend(server)


@click.group(help="Commands to manage compositions i.e. a collection of one or more subprojects")
def composition():
    pass


@composition.command(help="Initializes a new empty composition")
@click.argument(
    "path",
    type=click.Path(
        exists=False,
        dir_okay=True,
        file_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
@click.argument(
    "template_name",
    type=click.STRING,
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
    default=DEFAULT_MERGIN_SERVER,
    help="Specify non-default Mergin Maps Server",
)
def init(
    path: Path,
    template_name: str,
    name: str,
    workspace: str,
    server: str,
):
    Composition.initialize(
        path,
        template_name,
        name,
        workspace,
        server,
        mergin_backend(server),
    )


@composition.command(help="Creates a subproject from parcel specification and adds it to composition")
@click.argument(
    "composition",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    callback=resolve_composition_input,
)
@click.argument(
    "parcel_specification",
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
def add(
    composition: Path,
    parcel_specification: Path,
):
    comp = Composition.from_json(composition, mergin_backend(DEFAULT_MERGIN_SERVER))
    comp.add_subproject_from_parcelspec(parcel_specification)
    comp.save()


@composition.command(help="Uploads the given composition to the Mergin Maps server.")
@click.argument(
    "composition",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    callback=resolve_composition_input,
)
def upload(composition: Path):
    comp = Composition.from_json(composition, mergin_backend(DEFAULT_MERGIN_SERVER))
    comp.upload()


@composition.command(help="Uploads all subprojects in the composition to the Mergin Maps server.")
@click.argument(
    "composition",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    callback=resolve_composition_input,
)
def upload_subprojects(composition: Path):
    comp = Composition.from_json(composition, mergin_backend(DEFAULT_MERGIN_SERVER))
    comp.upload_subprojects()


@composition.command(
    help="Adds all GeoPackages from given directory to composition full data directory as symbolic links"
)
@click.argument(
    "composition",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=True,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    callback=resolve_composition_input,
)
@click.argument(
    "data_directory",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
    callback=str_to_path,
)
def link_data(
    composition: Path,
    data_directory: Path,
):
    comp = Composition.from_json(composition, mergin_backend(DEFAULT_MERGIN_SERVER))
    for file in data_directory.glob("*.gpkg"):
        # skip potential .gpkg-wal files etc.
        if not file.name.endswith(".gpkg"):
            continue

        os.symlink(file, comp.full_data_path() / f"{file.stem}.gpkg")


@composition.command(help="Downloads an existing composition from a Mergin Maps Server")
@click.argument(
    "path",
    type=click.Path(
        exists=False,
        dir_okay=True,
        file_okay=False,
        writable=True,
        readable=True,
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
    default=DEFAULT_MERGIN_SERVER,
    help="Specify non-default Mergin Maps Server",
)
def download(
    path: Path,
    name: str,
    workspace: str,
    server: str,
):
    client = mergin.MerginClient(login=os.getenv("MERGIN_USERNAME"), password=os.getenv("MERGIN_PASSWORD"), url=server)

    path.mkdir()
    composition_path = path / ".composition"

    client.download_project(
        f"{workspace}/{name}",
        composition_path,
    )

    composition_config_path = composition_path / "composition.json"
    comp = Composition.from_json(
        composition_config_path,
        mergin_backend(server),
        download_subprojects=True,
    )
    comp.download_template_project()
