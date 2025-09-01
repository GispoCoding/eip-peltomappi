#!/bin/bash

set -e

script_dir=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
repo_dir=$(readlink -f "$script_dir/..")
python_cli=$(readlink -f "$repo_dir/src/pm.py")

function _show_usage() {
  echo "Usage: $0 TEMPLATE_PROJECT_DIRECTORY FULL_DATA_DIRECTORY OUTPUT_DIRECTORY CONFIG_GPKG WORKSPACE PROJECT_NAME_PREFIX"
  echo -e "Splits a template project to parts and uploads them to a Mergin Maps server"
  echo -e "Arguments:"
  echo -e "\t TEMPLATE_PROJECT_DIRECTORY"
  echo -e "\t FULL_DATA_DIRECTORY"
  echo -e "\t OUTPUT_DIRECTORY: directory in which split projects are saved"
  echo -e "\t CONFIG_GPKG"
  echo -e "\t WORKSPACE"
  echo -e "\t PROJECT_NAME_PREFIX"
  echo -e "Options:"
  echo -e "\t -h, --help: show this message"
}

function _check_argument() {
  # $1 = argument name
  # $2 = argument value
  if [ "$2" == "" ]; then
    echo "ERROR: Argument $1 missing!"
    _show_usage
    exit 1;
  fi
}

# you could check that these exist, but the Python CLI does that anyway, so probably no point
template_project_dir=$1
full_data_dir=$2
output_dir=$3
config_gpkg=$4
workspace=$5
project_name_prefix=$6

# NOTE: this ordering does not really work, or at least wouldn't if there were
# any other accepted options, so if you add one, take that into account

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--help)
          _show_usage;
          exit 0;
          ;;
        --*) echo "ERROR: Unknown option passed: $1";
          _show_usage;
          exit 1;
          ;;
    esac
    shift
done

_check_argument "TEMPLATE_PROJECT_DIRECTORY" "$template_project_dir"
_check_argument "FULL_DATA_DIRECTORY" "$full_data_dir"
_check_argument "OUTPUT_DIRECTORY" "$output_dir"
_check_argument "CONFIG_GPKG" "$config_gpkg"
_check_argument "WORKSPACE" "$workspace"
_check_argument "PROJECT_NAME_PREFIX" "$project_name_prefix"


if [[ ! -n "$MERGIN_USERNAME" ]]; then
  echo "ERROR: MERGIN_USERNAME environment variable must be set"
  _show_usage
  exit
fi

if [[ ! -n "$MERGIN_PASSWORD" ]]; then
  echo "ERROR: MERGIN_PASSWORD environment variable must be set"
  _show_usage
  exit
fi

python3 "$python_cli" project split "$template_project_dir" "$full_data_dir" "$output_dir" "$config_gpkg"

for dir in $output_dir/*/; do
  if [ -d "$dir" ]; then
    project_name_suffix=$(basename "$dir")
    mergin create "$workspace/${project_name_prefix}_${project_name_suffix}" --from-dir="$dir"
  fi
done
