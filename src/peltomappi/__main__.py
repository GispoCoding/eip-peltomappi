import logging
import click

import peltomappi.cli.composition
from peltomappi.logger import LOGGER


@click.group(help="CLI tool to run Peltomappi commands")
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Only print out errors.",
)
def cli(quiet):
    if quiet:
        LOGGER.setLevel(logging.ERROR)


cli.add_command(peltomappi.cli.composition.composition)
