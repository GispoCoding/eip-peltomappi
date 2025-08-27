import click
import pathlib


def str_to_path(_, __, argument) -> pathlib.Path:
    return pathlib.Path(argument)


def validate_remove_field(_, __, argument) -> tuple[str] | None:
    if len(set(argument)) != len(argument):
        raise click.BadParameter(argument)

    return argument
