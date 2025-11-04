# Python documentation

## Background

The purpose of the EIP Peltomappi project is to provide a mapping tool for
farmers. Mergin Maps is used as the application for the mapping. However, this
tool is meant to be specific to one user or a small group of users and any
collected data is not meant to be centrally collected or shared. Therefore
using Mergin projects the "traditional" way, i.e. having a shared Mergin
project is not suitable for this use case. Additionally, local GeoPackage files
are required to provide background data for the project, which would make a
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
[Typer](https://typer.tiangolo.com/) based CLI.

### Installation

Create a Python virtual environment in a suitable folder:

```sh
python -m venv peltomappi_venv
```

Activate the virtual environment:

Windows (PowerShell):
```powershell
.\peltomappi_venv\Scripts\activate
```

Bash:
```sh
source peltomappi_venv/bin/activate
```

Download the packaged tool:

Windows (PowerShell):
```powershell
Invoke-WebRequest "https://github.com/GispoCoding/eip-peltomappi/releases/latest/download/peltomappi-alpha-py3-none-any.whl" -OutFile .\peltomappi-alpha-py3-none-any.whl
```

Bash (requires wget):
```sh
wget -q https://github.com/GispoCoding/eip-peltomappi/releases/latest/download/peltomappi-alpha-py3-none-any.whl
```

If the download commands do not work you may also download the file manually
[here](https://github.com/GispoCoding/eip-peltomappi/releases/latest/download/peltomappi-alpha-py3-none-any.whl).

Then either move the file to the directory or navigate to the download
directory in your shell.

Install the tool:

```sh
pip install peltomappi-alpha-py3-none-any.whl
```

Confirm that the tool was correctly installed:

```sh
peltomappi
```

You should see the following output:

```
Usage: peltomappi [OPTIONS] COMMAND [ARGS]...
Try 'peltomappi --help' for help.
╭─ Error ──────────╮
│ Missing command. │
╰──────────────────╯
```

!!! note
    The installation has to be done only once, after that it is available in
    the Python virtual environment. Remember to always activate the virtual
    environment, otherwise you will not have access to the tool.

### Authentication

To login run:

```
peltomappi login
```

To logout run:

```
peltomappi logout
```

### Commands

```sh
peltomappi --help
```

```
 Usage: peltomappi [OPTIONS] COMMAND [ARGS]...

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                        │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation. │
│ --help                        Show this message and exit.                                                      │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ init                         Initializes a new empty composition                                               │
│ add                          Creates a subproject from parcel specification and adds it to composition         │
│ push                         Pushes the local composition with its changes to the Mergin Server                │
│ pull                         Pulls changes from the Mergin Server to the local composition                     │
│ clone                        Downloads an existing composition from a Mergin Maps Server                       │
│ subprojects-match-template   Updates the configuration files of each subproject to match the template          │
│ subprojects-export-csv       Exports user data of each subproject to csv files                                 │
│ subprojects-update-weather   Updates weather data of each subproject                                           │
│ info                         Prints information about composition                                              │
│ login                        Authenticates username and password to Mergin Server and stores token to keyring  │
│ logout                       Removes token                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

#### Help

To get information about any command add the --help flag after it:

```sh
peltomappi init --help
```

Output:
```
 Usage: peltomappi init [OPTIONS] NAME

 Initializes a new empty composition

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    name      DIRECTORY  Path to new composition directory [required]                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --template        TEXT  Name of project in Mergin Server to use as a template project [required]    │
│ *  --workspace            TEXT  Workspace in the Mergin Server to use [required]                            │
│    --server               TEXT  Address of Mergin Server to connect to [default: https://app.merginmaps.com]│
│    --help                       Show this message and exit.                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

There are __arguments__ and __options__. Here _name_ is an __argument__ and is entered as is:

```sh
peltomappi init my_composition_name
```

However, _template_ and _workspace_ are __options__ and are entered like this:

```sh
peltomappi init my_composition_name --template=my_template_name --workspace=my_workspace
```

You can also skip the __=__ sign:

```sh
peltomappi init my_composition_name --template my_template_name --workspace my_workspace
```

Some options have a default value and are mandatory to enter, however you may override the default argument.

There are some _boolean options_ (also called flags):

```sh
peltomappi info --help
```

```
 Usage: peltomappi info [OPTIONS] COMPOSITION

 Prints information about composition

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────╮
│ *    composition      EXISTING_COMPOSITION  Path to existing composition directory [required]     │
╰───────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────╮
│ --subproj    --no-subproj      Print information about subprojects [default: subproj]             │
│ --help                         Show this message and exit.                                        │
╰───────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Flags do not require giving a value:

```sh
peltomappi info --no-subproj my_composition
```

### Examples

#### Initializing a composition

```sh
peltomappi init my_composition --template=my_template --workspace=my_workspace
```

The template option corresponds to an existing project in the Mergin Maps
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
peltomappi clone composition_name_in_server path_of_cloned_directory --workspace=my_workspace
```

!!! note
    This step may take a while, since the full data folder is also downloaded,
    which can be quite large.

#### Examining a composition

You can print out information about a locally existing composition:

```sh
peltomappi info my_composition
```

If you don't want information about subprojects to be printed out you can add
the `--no-subproj` flag.

```sh
peltomappi info my_composition --no-subproj
```

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
peltomappi add parcelspec.json my_composition
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
peltomappi pull my_composition
```

#### Making modifications

Before making modifications remember to check that you have the latest changes
and [pull](#pulling-modifications) if necessary!

The purpose of the peltomappi CLI tool is to centrally control all of the
subprojects. Subprojects should generally **never** be individually modified.

Instead you should make any changes to the **template** project, save them and
update the changes to the subprojects using the CLI:

```sh
peltomappi subprojects-match-template my_composition
```

!!! note
    This only updates the local versions of the subprojects, for the changes to
    take effect for the users, the changes must be pushed to the Mergin Server.

#### Pushing modifications

Push by running:

```sh
peltomappi push my_composition
```

Pushing will update any modified files to the subprojects in the Mergin Server,
but also create and upload the subproject if it does not already exist. The
same happens to the composition itself. Changes to the template project are
also pushed.

!!! note
    If you are pushing the composition for the first time, the full data is
    also uploaded to the server, which may take a long time.

#### Export user data to csv

```sh
peltomappi subprojects-export-csv my_composition
```

#### Non-default server

When cloning or initializing a composition the CLI will by default use the official
Mergin Server at [https://app.merginmaps.com](https://app.merginmaps.com). If you need to
use another server, you may append the `--server` option to the commands:

```sh
peltomappi login --server=http://localhost:8080
```

```sh
peltomappi init --server=http://localhost:8080 my_composition --template=my_template --workspace=my_workspace
```

```sh
peltomappi clone --server=http://localhost:8080 composition_name_in_server path_of_cloned_directory --workspace=my_workspace
```

!!! note
    In other commands (i.e. when not creating a new composition) the server is
    read from the `composition.json` file and cannot be modified in the command.

## Library

Here is the auto-generated documentation of the `peltomappi` package/library:

### Module: composition

::: src.peltomappi.composition

### Module: subproject

::: src.peltomappi.subproject

### Module: parcelspec

::: src.peltomappi.parcelspec

### Module: filter

::: src.peltomappi.filter

### Module: utils

::: src.peltomappi.utils
