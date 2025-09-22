from pathlib import Path
import click

from peltomappi.cli.utils import resolve_composition_input, str_to_path
from peltomappi.composition import Composition, MerginBackend


DEFAULT_MERGIN_SERVER = "https://app.merginmaps.com"
g_mergin_server = DEFAULT_MERGIN_SERVER


def mergin_backend(server: str) -> MerginBackend:
    return MerginBackend(server)


@click.group(help="Commands to manage compositions i.e. a collection of one or more subprojects")
@click.option(
    "--server",
    type=click.STRING,
    default=DEFAULT_MERGIN_SERVER,
    help="Specify non-default Mergin Maps Server",
)
def composition(server):
    global g_mergin_server
    g_mergin_server = server


@composition.command(help="Initializes a new empty composition")
@click.argument(
    "name",
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
    "workspace",
    type=click.STRING,
)
def init(
    name: Path,
    template_name: str,
    workspace: str,
):
    Composition.initialize(
        name,
        template_name,
        name.stem,
        workspace,
        g_mergin_server,
        mergin_backend(g_mergin_server),
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
    comp = Composition.from_json(composition, mergin_backend(g_mergin_server))
    comp.add_subproject_from_parcelspec(parcel_specification)
    comp.save()


@composition.command(help="Pushes the local composition with its changes to the Mergin Server")
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
def push(composition: Path):
    comp = Composition.from_json(composition, mergin_backend(g_mergin_server))
    comp.push()


@composition.command(help="Pulls changes from the Mergin Server to the local composition")
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
def pull(composition: Path):
    comp = Composition.from_json(composition, mergin_backend(g_mergin_server))
    comp.pull()


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
def clone(
    path: Path,
    name: str,
    workspace: str,
):
    Composition.clone(
        path,
        name,
        workspace,
        mergin_backend(g_mergin_server),
    )


@composition.command(help="Updates the configuration files of each subproject to match the template")
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
def subprojects_match_template(composition: Path):
    comp = Composition.from_json(composition, mergin_backend(g_mergin_server))
    comp.subprojects_match_template()
