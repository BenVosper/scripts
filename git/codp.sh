#!/bin/sh
#
# =================================================================================================
#
# comp (Checkout-master, pull)
#
# A script for keeping local default branch of repos up to date with the remote.
#
# Usage:
#
# In the directory containing your repos, run the script with a path to your repos file.
# This file should be a text file with a number of lines of the form:
#
# <Repo URL> <Directory to clone into> (<Name of conda environment to create>)
#                                                 ^ Optional
# Lines starting with "#" are ignored.
#
# For each line in the repos file, we check if there are uncommitted changes for that repo.
# If the index is clean, we checkout master and pull from the remote.
#
# =================================================================================================


comp () {
    repo_url=$1
    repo_dir=$2

    if [ ! -d "$PWD/$repo_dir" ]; then
        echo "Repo directory does not exist: $repo_dir..."
        return
    fi

    (
        cd "$repo_dir"
        if git diff-index --quiet HEAD; then
            default_branch=$(git rev-parse --abbrev-ref origin/HEAD | cut -d'/' -f2)
            echo "$repo_dir is clean. Updating $default_branch..."
            git fetch
            git checkout "$default_branch"
            git pull
        else
            echo "$repo_dir is dirty. Skipping..."
        fi
    )
}

if [ $1 = "-h" -o $1 = "--help" ]; then
    echo "Usage: codp /path/to/repos.txt"
    return
fi

cat $1 | grep "^[^#]" | while read line; do
    comp $line
done


echo "All done!"
