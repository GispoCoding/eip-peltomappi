import click
import pathlib


def str_to_path(_, __, argument) -> pathlib.Path:
    return pathlib.Path(argument)


def resolve_composition_input(_, __, argument) -> pathlib.Path:
    composition = str_to_path("", "", argument)
    if composition.is_dir():
        if (composition / "composition.json").exists():
            composition = composition / "composition.json"
        elif (composition / ".composition/composition.json").exists():
            composition = composition / ".composition/composition.json"

    return composition


def validate_remove_field(_, __, argument) -> tuple[str] | None:
    if len(set(argument)) != len(argument):
        raise click.BadParameter(argument)

    return argument
