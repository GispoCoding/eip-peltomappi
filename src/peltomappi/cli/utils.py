import click
import pathlib
from typing import Callable

from peltomappi.prefix import PrefixType


def str_to_path(_, __, argument) -> pathlib.Path:
    return pathlib.Path(argument)


def validate_remove_field(_, __, argument) -> tuple[str] | None:
    if len(set(argument)) != len(argument):
        raise click.BadParameter(argument)

    return argument


def prefixtype_to_callback(_, __, argument) -> Callable[[str], str] | None:
    if argument is None:
        return None

    # PrefixType should store functions in a 1-long tuple,
    # retrieve the function by accessing the enum by the user-given
    # string and getting the actual function from the first index
    # of the matching enum value
    return PrefixType[argument].value[0]
