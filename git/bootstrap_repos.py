import argparse
import json

from os import chdir, listdir, mkdir
from os.path import exists, split, join
from subprocess import run


def parse_settings(path):
    with open(path) as f:
        return json.load(f)


def init_install_directory(path):
    if not exists(path):
        mkdir(path)
    chdir(path)


def get_existing_conda_envs(command):
    conda_list_command = run(command.split(" "), capture_output=True, check=True)
    env_paths = json.loads(conda_list_command.stdout)["envs"]
    return [split(path)[-1] for path in env_paths]


def clone_repo(repo_dict):
    run(["git", "clone", repo_dict["url"], repo_dict["directory_name"]], check=True)


def create_conda_env(command, packages, env_name):
    args = command.split(" ") + [env_name] + packages.split(" ")
    run(args, check=True)


def install_python_dependencies(activate_command, env_name, pip_command, deactivate_command):
    args = activate_command + " " + env_name
    args += " && "
    args += pip_command
    args += " && "
    args += deactivate_command
    run(args, check=True, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap repos")
    parser.add_argument("settings", help="Path to settings JSON")

    args = parser.parse_args()

    settings = parse_settings(args.settings)
    existing_conda_envs = get_existing_conda_envs(settings["conda_list_command"])

    install_directory = settings["install_directory"]
    init_install_directory(install_directory)
    existing_directories = listdir(install_directory)

    for repo_dict in settings["repos"]:
        directory_name = repo_dict["directory_name"]
        print(f"Setting-up repo: {directory_name}...")

        if directory_name not in existing_directories:
            print(f"Cloning {directory_name}...")
            clone_repo(repo_dict)
        else:
            print(f"Skipping cloning {directory_name}...")

        env_name = repo_dict.get("conda_env", None)
        if not env_name:
            continue

        if env_name not in existing_conda_envs:
            print(f"Creating conda environment: {env_name}...")
            create_conda_env(
                settings["conda_create_command"],
                settings["conda_create_packages"],
                env_name
            )
        else:
            print(f"Skipping creating conda environment: {env_name}...")

        chdir(join(install_directory, directory_name))

        print(f"Installing python requirements for {directory_name}...")
        install_python_dependencies(
            settings["conda_activate_command"],
            env_name,
            settings["pip_command"],
            settings["conda_deactivate_command"]
        )

    print("All done!")
