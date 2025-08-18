#!/usr/bin/env python3

import logging
import pathlib

import click

from peltomappi.downloader import Downloader
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


@click.group(help="Commands to manage Peltomappi projects")
def project():
    pass


def convert_download_data(_, __, value) -> Downloader.Type:
    return Downloader.Type[value]


def convert_output_directory(_, __, value) -> pathlib.Path:
    return pathlib.Path(value)


@click.command(help="Downloads data used in a Peltomappi project")
@click.argument(
    "data",
    type=Downloader.Type.to_choice(),
    callback=convert_download_data,
)
@click.argument(
    "output_directory",
    type=click.Path(
        exists=True,
        dir_okay=True,
        file_okay=False,
        readable=True,
        writable=True,
        resolve_path=True,
    ),
    callback=convert_output_directory,
)
def download(data, output_directory):
    downloader = Downloader(data, output_directory)
    downloader.run()


@project.command(help="Creates a new Peltomappi project")
def create():
    LOGGER.error("unimplemented command")


if __name__ == "__main__":
    cli.add_command(download)
    cli.add_command(project)

    cli()
