# Python documentation

## Background

The purpose of the EIP Peltomappi project is to provide a mapping tool for
farmers. Mergin Maps is used as the application for the mapping. However, this
tool is meant to be specific to one user or a small group of users and any
collected data is not meant to be centrally collected or shared. Therefore
using Mergin projects the "traditional" way, i.e. having a shared project is
not suitable for this project. Additionally, local GeoPackage files are
required to provide background data for the project, which would make the
shared project impractically large in disk size.

Mergin offers a partial solution with [Work
Packages](https://merginmaps.com/docs/dev/work-packages/), but with the
addition of a requirement to periodically update meteorological data and
possibly other specialized data processing and update workflows there was a
clear requirement for a tool to manage Peltomappi projects.

## Concepts

### Template project

A template project is the basis of [_subprojects_](#subproject). It is
the project which is manually modified in QGIS.

The template project can (and should) contain some data for ease of use, but
not the [full data](#full-data).

### Subproject

A subproject is the folder containing the Mergin Maps files and data of one
user / group of users. A subproject is based on the template project and is
automatically generated.

Subprojects should **not** be modified manually, barring exceptional
circumstances.

When creating a subproject, a list of field parcel IDs is defined. They are
used to spatially filter the full data, meaning that a subproject contains
only data from around the given field parcels.

A subproject exists in the Mergin Server, from which it can be used by its
user(s).

### Full data

This is a folder containing all of the initial background data, which is
filtered into subprojects.

### Composition

A composition is a unit containing all of the above. In practice, it is a folder
with the following structure:

    <folder>
    ├── .composition
    │   ├── composition.json
    │   └── full_data
    │       └── <data-gpkg>
    ├── <subproject-name> (0..N)
    │   ├── peltomappi_subproject.json
    │   └── etc ...
    └── <template-name>
        ├── <data-gpkg>
        └── etc ...

A composition therefore is a collection of a template project, subprojects, and
the full data.

A composition should also exist in the Mergin Server. In this case, the
`.composition` folder and its contents are uploaded as the "project" i.e. the
subprojects and the template projects are not included in the Mergin Server
composition "project", since in order for them to be usable they must be
individual projects.

Compositions are designed to be shareable, such that multiple people can
independently manage one composition. The `composition.json` file contains
information about its structure, which enables multiple people to _clone_ the
same composition locally, and pushing their modifications back to the Mergin
Server.

### Modifications

Out of all of the units mentioned above, **only** template projects should be
modified "by-hand", i.e. editing the project in QGIS. In order to modify
subprojects and compositions a programmatic tool should be used.

This is detailed in the next section.

## Command Line Interface

The functionality of the Python package is exposed through a
[Click](https://click.palletsprojects.com/en/stable/) based CLI.

!!! note
    At the current stage of development the peltomappi tool is not packaged. In
    order to use the CLI you have to create and activate a Python virtual
    environment (or install its dependencies system-wide, but this is not
    recommended).

    For instructions see the [README](https://github.com/GispoCoding/eip-peltomappi).

The entrypoint to the CLI is in `src/pm.py`. In order to run peltomappi commands
run the `pm.py` script:

```sh
python pm.py --help
```

```
Usage: pm.py [OPTIONS] COMMAND [ARGS]...

  CLI tool to run Peltomappi commands

Options:
  -q, --quiet  Only print out errors.
  --help       Show this message and exit.

Commands:
  composition  Commands to manage compositions i.e.
```

### Commands

Currently there is only one main command, `composition`.

```sh
python pm.py composition --help
```

```
Usage: pm.py composition [OPTIONS] COMMAND [ARGS]...

  Commands to manage compositions i.e. a collection of one or more subprojects

Options:
  --server TEXT  Specify non-default Mergin Maps Server
  --help         Show this message and exit.

Commands:
  add                         Creates a subproject from parcel...
  clone                       Downloads an existing composition from a...
  init                        Initializes a new empty composition
  pull                        Pulls changes from the Mergin Server to the...
  push                        Pushes the local composition with its...
  subprojects-match-template  Updates the configuration files of each...
```

The `composition` command has several subcommands:

* add: Creates a subproject from parcel specification and adds it to composition
* clone: Downloads an existing composition from a Mergin Maps Server
* init: Initializes a new empty composition
* pull: Pulls changes from the Mergin Server to the local composition
* push: Pushes the local composition with its changes to the Mergin Server
* subprojects-match-template: Updates the configuration files of each subproject to match the template

### Authentication

For authentication set the `MERGIN_USERNAME` and `MERGIN_PASSWORD` environment variables.

Bash:
```bash
export MERGIN_USERNAME="<value>"
export MERGIN_PASSWORD="<value>"
```

PowerShell:
```powershell
$env:MERGIN_USERNAME = ""
$env:MERGIN_PASSWORD = ""
```

### Examples

#### Initializing a composition

```sh
python pm.py composition init <composition_name> <template_name> <workspace_name>
```

```sh
python pm.py composition init my_composition my_template my_workspace
```

The template argument corresponds to an existing project in the Mergin Maps
server, meaning it should be created and uploaded prior to creating a
composition using it. You can do this manually, with the QGIS plugin or with
the Mergin client CLI:

```sh
mergin create my_workspace/my_template --from-dir=template_directory
```

!!! important
    Currently the full data files must be manually copied to the composition! Copy them to the
    `my_composition/.composition/full_data` folder!

#### Cloning an existing composition

If a composition has already been created and is pushed to the Mergin Server, you can
clone it to your local machine:

```sh
python pm.py composition clone <folder_name> <name> <mergin_workspace>
```

```sh
python pm.py composition clone local_composition my_composition my_workspace
```

!!! note
    This step may take a while, since the full data folder is also downloaded,
    which can be quite large.

#### Adding subprojects to a composition

Subprojects are created from a parcel specification. In practice this is a JSON
file. Currently they must be created by hand. The parcel specification must
adhere to a simple JSON schema.

Create a parcel specification in a text editor and save it as a JSON file. You
can use this as a template:

```json
{
    "name": "this_will_be_the_subproject_name",
    "fieldParcelIds": [
        "1111111111",
        "2222222222",
        "3333333333"
    ]
}
```

Once you have saved the parcel specification JSON, you can create a subproject
and add it to a composition:

```sh
python pm.py composition add <composition> <parcel_spec_json>
```

```sh
python pm.py composition add my_composition parcelspec.json
```

Here `my_composition` being the folder which was created by the `init` or
`clone` command.

!!! note
    After adding a subproject, you likely should invite a user to the
    subproject. Currently this must be done manually, through the Mergin Server web
    interface.


#### Pulling modifications

Compositions are designed to be shareable, i.e. others might have updated one
without it automatically synchronizing to your local composition. Additionally
users might make changes to their subprojects. Therefore, whenever planning to
make changes to the template project you should ensure that you have the
latest changes in your local composition.

```sh
python pm.py composition pull my_composition
```

#### Making modifications

Before making modifications remember to check that you have the latest changes
and [pull](#pulling-modifications) if necessary!

The purpose of the peltomappi CLI tool is to centrally control all of the
subprojects. Subprojects should generally **never** be individually modified.

Instead you should make any changes to the **template** project, save them and
update the changes to the subprojects using the CLI:

```sh
python pm.py composition subprojects-match-template my_composition
```

!!! note
    This only updates the local versions of the subprojects, for the changes to
    take effect for the users, the changes must be pushed to the Mergin Server.

#### Pushing modifications

Push by
running:

```sh
python pm.py composition push my_composition
```

Pushing will update any modified files to the subprojects in the Mergin Server,
but also create and upload the project if it does not already exist.

!!! note
    If you are pushing the composition for the first time, the full data is
    also uploaded to the server, which may take a long time.

#### Non-default server

By default the CLI will attempt to connect to
[https://app.merginmaps.com](https://app.merginmaps.com). If you need to
connect to another server, you may append the `--server` option to the
composition command:

```sh
python pm.py composition --server=http://localhost:8080 push my_composition
```

!!! note
    The option must be specified after `composition` but before the subcommand, i.e. `push`, `pull` etc.

## Library

Here is the auto-generated documentation of the `peltomappi` package/library:

::: src.peltomappi.composition

::: src.peltomappi.subproject

::: src.peltomappi.parcelspec

::: src.peltomappi.filter

::: src.peltomappi.utils
