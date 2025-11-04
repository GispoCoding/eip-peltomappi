from getpass import getpass
from typing import Annotated
import mergin.cli
import typer

from peltomappi.composition import Composition, MerginBackend

from pathlib import Path

DEFAULT_MERGIN_SERVER = "https://app.merginmaps.com"


def mergin_backend(server: str) -> MerginBackend:
    return MerginBackend(server)


def existing_composition(in_value: str) -> Path:
    composition = Path(in_value)
    if (composition / "composition.json").exists():
        composition = composition / "composition.json"
    elif (composition / ".composition/composition.json").exists():
        composition = composition / ".composition/composition.json"
    else:
        msg = f"{in_value} does not seem to be a valid path to a composition"
        raise typer.BadParameter(msg)

    return composition


ExistingCompositionPath = Annotated[
    Path,
    typer.Argument(
        parser=existing_composition,
        help="Path to existing composition directory",
        exists=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
        readable=True,
    ),
]


NewCompositionPath = Annotated[
    Path,
    typer.Argument(
        help="Path to new composition directory",
        exists=False,
        file_okay=False,
        writable=True,
        resolve_path=True,
    ),
]

Server = Annotated[
    str,
    typer.Option(
        help="Address of Mergin Server to connect to",
    ),
]

Workspace = Annotated[
    str,
    typer.Option(
        help="Workspace in the Mergin Server to use",
    ),
]

app = typer.Typer()


@app.command(help="Initializes a new empty composition")
def init(
    name: NewCompositionPath,
    template_name: Annotated[str, typer.Option(help="Name of project in Mergin Server to use as a template project")],
    workspace: Workspace,
    server: Server = DEFAULT_MERGIN_SERVER,
):
    Composition.initialize(
        name,
        template_name,
        name.stem,
        workspace,
        server,
        mergin_backend(server),
    )


def main() -> None:
    app()


@app.command(help="Creates a subproject from parcel specification and adds it to composition")
def add(
    parcel_specification: Annotated[
        Path,
        typer.Argument(file_okay=True, dir_okay=False, exists=True, resolve_path=True, readable=True),
    ],
    composition: ExistingCompositionPath,
):
    comp = Composition.from_json(composition)
    comp.add_subproject_from_parcelspec(parcel_specification)
    comp.save()


@app.command(help="Pushes the local composition with its changes to the Mergin Server")
def push(
    composition: ExistingCompositionPath,
):
    comp = Composition.from_json(composition)
    comp.push()


@app.command(help="Pulls changes from the Mergin Server to the local composition")
def pull(
    composition: ExistingCompositionPath,
):
    comp = Composition.from_json(composition)
    comp.pull()


@app.command(help="Downloads an existing composition from a Mergin Maps Server")
def clone(
    name: Annotated[str, typer.Argument(help="Name of composition project in the Mergin Server")],
    path: NewCompositionPath,
    workspace: Workspace,
    server: Server = DEFAULT_MERGIN_SERVER,
):
    Composition.clone(
        path,
        name,
        workspace,
        mergin_backend(server),
    )


@app.command(help="Updates the configuration files of each subproject to match the template")
def subprojects_match_template(
    composition: ExistingCompositionPath,
):
    comp = Composition.from_json(composition)
    comp.subprojects_match_template()


@app.command(help="Exports user data of each subproject to csv files")
def subprojects_export_csv(composition: Path):
    comp = Composition.from_json(composition)
    comp.subprojects_export_csv()


@app.command(help="Updates weather data of each subproject")
def subprojects_update_weather(composition: Path):
    comp = Composition.from_json(composition)
    comp.subprojects_update_weather()


@app.command(help="Prints information about composition")
def info(
    composition: ExistingCompositionPath,
    subproj: Annotated[
        bool,
        typer.Option(
            help="Print information about subprojects",
            is_flag=True,
        ),
    ] = True,
):
    comp = Composition.from_json(composition)
    comp.describe(describe_subprojects=subproj)


if __name__ == "__main__":
    main()


@app.command(help="Authenticates username and password to Mergin Server and stores token to keyring")
def login(
    server: Server = DEFAULT_MERGIN_SERVER,
):
    username: str = input("Username: ")
    pwd: str = getpass("Password: ")

    token = mergin.cli.get_token(url=server, username=username, password=pwd)

    if not isinstance(token, str):
        msg = "token is not string"
        raise ValueError(msg)

    token = f"Bearer {token}"

    import keyring

    keyring.set_password("system", "peltomappi_cli_authentication_token", token)


@app.command(help="Removes token")
def logout():
    import keyring

    keyring.delete_password("system", "peltomappi_cli_authentication_token")
