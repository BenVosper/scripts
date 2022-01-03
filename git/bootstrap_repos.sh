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
# Set the VENV_DIR environment variable to where you'd like your environments to live.
#
# Ensure that any python versions required by your repos are available on your PATH
# and called using 'pythonX.Y'.
#
# In the directory into which you'd like to clone the repos, run the script with a path to your
# repos file. This file should be a text file with a number of lines of the form:
#
# <Repo URL> <Directory to clone into> (<Name of venv to create>) (<Python version>)
#                                                 ^ Optional       ^ Optional
# Lines starting with "#" are ignored.
#
# For each line in the repos file, we then:
#    1. Clone the specified repo into the given directory, if it doesn't already exist
#    2. Create a venv with the given name, if one doesn't already exist
#    3. Install python dependencies listed in requirements.txt file in each repo directory
#
# The commands for each of these steps can be modified for your system in the block below.

INITIAL_ENV_PACKAGES="ipython"
# =================================================================================================

EXISTING_ENVS=$(ls -d "$VENV_DIR"/*/)


echo_highlight () {
  HIGHLIGHT="\033[1;92m"
  CLEAR_HIGHLIGHT='\033[0m'
  echo -e "${HIGHLIGHT}$1${CLEAR_HIGHLIGHT}"
}


bootstrap () {
    repo_url=$1
    repo_dir=$2
    venv_name=$3
    python_version=$4

    if [[ -z $(which "python$python_version" 2>\dev\null) ]]; then
        echo_highlight "Python version $python_version not found. Exiting..."
        exit
    fi

    if [[ ! -d "$PWD/$repo_dir" ]]; then
        echo_highlight "Cloning $repo_dir..."
        git clone "$repo_url" "$repo_dir"
    else
        echo_highlight "Repo directory already exists: $repo_dir..."
    fi

    # Exit early if we don't need a venv
    if [[ -z "$venv_name" ]]; then
        return
    fi

    if grep -q "$venv_name" <<< $EXISTING_ENVS; then
        echo_highlight "Virtual environment already exists: $venv_name..."
    else
        echo_highlight "Creating virtual environment: $venv_name..."
        eval "python$python_version -m venv $VENV_DIR/$venv_name"
    fi

    # Exit early if we can't find requirements file
    if [[ ! -e "$repo_dir/requirements.txt" ]]; then
        echo_highlight "No requirements.txt file found in $repo_dir."
        return
    fi

    echo_highlight "Installing python requirements for $repo_dir..."
    (
        cd "$repo_dir" &&
        source "$VENV_DIR/$venv_name/bin/activate" &&
        pip install --upgrade pip
        pip install -r requirements.txt &&
        pip install "$INITIAL_ENV_PACKAGES"
        deactivate
    )
}

if [[ $1 == "-h" ]] || [[ $1 == "--help" ]]; then
    echo "Usage: bootstrap_repos /path/to/repos.txt"
    return
fi

cat $1 | grep "^[^#]" | while read line; do
    bootstrap $line
done

echo_highlight "All done!"
