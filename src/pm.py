#!/usr/bin/env python3

import click


@click.group(help="CLI tool to run Peltomappi processes")
def cli():
    pass


@click.command(help="Creates a Peltomappi project")
def create():
    print("create")


if __name__ == "__main__":
    cli.add_command(create)
    cli()
