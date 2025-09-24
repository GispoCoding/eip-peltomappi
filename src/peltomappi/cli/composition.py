from pathlib import Path
import click

from peltomappi.cli.utils import resolve_composition_input, str_to_path
from peltomappi.composition import Composition, MerginBackend

from getpass import getpass

import mergin.cli


DEFAULT_MERGIN_SERVER = "https://app.merginmaps.com"


def mergin_backend(server: str) -> MerginBackend:
    return MerginBackend(server)


@click.group(help="Commands to manage compositions i.e. a collection of one or more subprojects")
def composition():
    pass


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
@click.option(
    "--server",
    type=click.STRING,
    default=DEFAULT_MERGIN_SERVER,
    help="Specify non-default server",
)
def init(
    name: Path,
    template_name: str,
    workspace: str,
    server: str,
):
    Composition.initialize(
        name,
        template_name,
        name.stem,
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
    comp = Composition.from_json(composition)
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
    comp = Composition.from_json(composition)
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
    comp = Composition.from_json(composition)
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
@click.option(
    "--server",
    type=click.STRING,
    default=DEFAULT_MERGIN_SERVER,
    help="Specify non-default server",
)
def clone(
    path: Path,
    name: str,
    workspace: str,
    server: str,
):
    Composition.clone(
        path,
        name,
        workspace,
        mergin_backend(server),
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
    comp = Composition.from_json(composition)
    comp.subprojects_match_template()


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
def subprojects_export_csv(composition: Path):
    comp = Composition.from_json(composition)
    comp.subprojects_export_csv()


@composition.command(help="Prints information about composition")
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
@click.option(
    "--only-composition",
    type=click.BOOL,
    default=True,
    is_flag=True,
    help="Don't print subproject info",
)
def info(composition: Path, only_composition: bool):
    comp = Composition.from_json(composition)
    comp.describe(describe_subprojects=only_composition)


@composition.command(help="Logs into Mergin Server")
@click.option(
    "--server",
    type=click.STRING,
    default=DEFAULT_MERGIN_SERVER,
    help="Specify non-default server",
)
def login(server: str):
    username: str = input("Username: ")
    pwd: str = getpass("Password: ")

    token = mergin.cli.get_token(url=server, username=username, password=pwd)

    if not isinstance(token, str):
        msg = "token is not string"
        raise ValueError(msg)

    token = f"Bearer {token}"

    import keyring

    keyring.set_password("system", "peltomappi_cli_authentication_token", token)


@composition.command(help="Removes token")
def logout():
    import keyring

    keyring.delete_password("system", "peltomappi_cli_authentication_token")
