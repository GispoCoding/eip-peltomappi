#!/usr/bin/env python3

import logging
import click

from peltomappi.logger import LOGGER


@click.group(help="CLI tool to run Peltomappi processes")
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Only print out errors.",
)
def cli(quiet):
    if quiet:
        LOGGER.setLevel(logging.ERROR)


if __name__ == "__main__":
    # cli.add_command(peltomappi.cli.weather.weather)
    # cli.add_command(peltomappi.cli.composition.composition)

    cli()
