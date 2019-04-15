import argparse
import json

from os import chdir
from os.path import join
from subprocess import run


def parse_settings(path):
    with open(path) as f:
        return json.load(f)


def repo_is_clean():
    """Check if there are uncommitted changes in current working directory."""
    process = run(["git", "diff-index", "--quiet", "HEAD"])
    return process.returncode == 0


def update_master():
    """Pull most-recent master branch of repo in current working directory,"""
    run(["git", "fetch"])
    run(["git", "checkout", "master"])
    run(["git", "pull"])


def main():
    parser = argparse.ArgumentParser(description="Bootstrap repos")
    parser.add_argument("settings", help="Path to settings JSON")

    args = parser.parse_args()

    settings = parse_settings(args.settings)
    install_directory = settings["install_directory"]

    for repo_dict in settings["repos"]:
        directory_name = repo_dict["directory_name"]
        chdir(join(install_directory, directory_name))

        if repo_is_clean():
            print(f"{directory_name} is clean. Updating master...")
            update_master()
        else:
            print(f"{directory_name} is dirty. Skipping...")
            continue

    print("All done!")


if __name__ == "__main__":
    main()
