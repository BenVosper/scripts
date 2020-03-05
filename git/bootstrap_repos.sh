#!/usr/bin/env bash
#
# =================================================================================================
#
# bootstrap_repos
#
# A script for initialising git repositories and python environments described by a text file.
#
# Usage:
#
# In the directory into which you'd like to clone the repos, run the script with a path to your
# repos file. This file should be a text file with a number of lines of the form:
#
# <Repo URL> <Directory to clone into> (<Name of conda environment to create>)
#                                                 ^ Optional
# Lines starting with "#" are ignored.
#
# For each line in the repos file, we then:
#    1. Clone the specified repo into the given directory, if it doesn't already exist
#    2. Create a conda env with the given name, if one doesn't already exist
#    3. Install python dependencies listed in requirements.txt file in each repo directory
#
# The commands for each of these steps can be modified for your system in the block below.

CONDA_LIST_COMMAND="conda env list"
CONDA_CREATE_COMMAND="conda create -y -n"
CONDA_ACTIVATE_COMMAND="conda activate"
CONDA_DEACTIVATE_COMMAND="conda deactivate"
INITIAL_ENV_PACKAGES="pip"
PIP_COMMAND="pip install -r requirements.txt"

# =================================================================================================

EXISTING_ENVS=$(eval $CONDA_LIST_COMMAND | grep "^[^#]" | awk '{ print $1 }')


bootstrap () {
    repo_url=$1
    repo_dir=$2
    conda_env=$3
    python_version=$4

    if [[ ! -d "$PWD/$repo_dir" ]]; then
        echo "Cloning $repo_dir..."
        git clone "$repo_url" "$repo_dir"
    else
        echo "Repo directory already exists: $repo_dir..."
    fi

    # Exit early if we don't need a conda env
    if [[ -z "$conda_env" ]]; then
        return
    fi

    if grep -q "$conda_env" <<< $EXISTING_ENVS; then
        echo "Conda environment already exists: $conda_env..."
    else
        echo "Creating conda environment: $conda_env..."
        eval "$CONDA_CREATE_COMMAND $conda_env python==$python_version $INITIAL_ENV_PACKAGES"
    fi

    # Exit early if we can't find requirements file
    if [[ ! -e "$repo_dir/requirements.txt" ]]; then
        echo "No requirements.txt file found in $repo_dir."
        return
    fi

    echo "Installing python requirements for $repo_dir..."
    (
        cd "$repo_dir" &&
        eval "$CONDA_ACTIVATE_COMMAND $conda_env" &&
        eval "$PIP_COMMAND" &&
        eval "$CONDA_DEACTIVATE_COMMAND"
    )
}

if [[ $1 == "-h" ]] || [[ $1 == "--help" ]]; then
    echo "Usage: bootstrap_repos /path/to/repos.txt"
    return
fi

cat $1 | grep "^[^#]" | while read line; do
    bootstrap $line
done

echo "All done!"
