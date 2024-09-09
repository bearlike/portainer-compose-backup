#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Version Backup all docker compose scripts created within Portainer.
    For more information, see: README.md
"""
from collections import defaultdict
import subprocess
import datetime
import logging
import shutil
import json
import os
from git import Repo
from utils import get_current_module_path
import load_env_to_db as env2db

logging.basicConfig(
    filename="portainer_backups.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p,\t\t",
    encoding="utf-8",
)


def execute_cmd(cmd):
    """
    Executes a shell command and returns the output to a string
    """
    output = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    if output is None or output == "":
        output = "No output"
    logging.info("Shell Output: %s", output.strip())


def create_directory(path):
    """Create a directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)


def copy_files(src, dest, mode=1):
    """
    Copy all files from src directory to dest directory.
    If dest directory does not exist, it will be created.
    """
    try:
        if os.path.exists(dest):
            shutil.rmtree(dest)
        create_directory(path=dest)
        # dirs_exist_ok=True is only available in Python >=3.8
        if mode == 2:
            logging.info("Using copy mode 2 - bash copy")
            # ! This is a hack to copy files from docker volume to host
            # !   since shutil.copytree() does not work probably because of
            # !   permission issues.
            execute_cmd(cmd=f"cp -r { src }/* { dest }")
        else:
            logging.info("Using copy mode 1 - shutil copy")
            shutil.copytree(src, dest)
        logging.info("Successfully copied files from %s to %s", src, dest)
    # pylint: disable=W0718
    except Exception as error:
        logging.error("Error occurred while copying files: %s", str(error))


def git_commit_push(repo_path, commit_message):
    """
    Perform git commit and git push in the given repo_path.
    """
    try:
        repo = Repo(repo_path)
        repo.git.add(repo_path + "/backups")
        repo.git.add(repo_path + "/portainer_backups.log")
        repo.git.add(repo_path + "/stack.encrypted.json")
        repo.index.commit(commit_message)
        origin = repo.remote(name="origin")
        origin.push()
        logging.info("Successfully pushed to repo")
    # pylint: disable=W0718
    except Exception as error:
        logging.error("Error occurred while pushing to repo: %s", str(error))


def get_dates():
    """
    Get the current year, month and day.
    """
    current_date = datetime.date.today()
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day
    return current_year, current_month, current_day


def generate_dest_path(project_directory):
    """
    Generate the destination path for the backup files.
    """
    current_year, current_month, current_day = get_dates()
    path_time_substring = f"{current_year}/{current_month:02}/{current_day:02}"
    dest = f"{ project_directory }/backups/{ path_time_substring }"
    return dest


def process_backed_up_files(metadata, path):
    """Process the backed up files.

    Args:
        metadata (defaultdict): Generated from the Portainer BoltDB database.
        path (str): Path of the backed up files.
    """
    compose_folders = set(os.listdir(path))
    logging.info("Compose folders: %s", str(compose_folders))
    # Create a directory structure for each endpoint
    for _host_id in metadata["endpoints"]:
        _host_name = metadata["endpoints"][_host_id]["name"]
        create_directory(path=f"{path}/{_host_name}")

        # Create a directory structure for each stack
        for _stacks_id in metadata["endpoints"][_host_id]["stacks"]:
            _stacks_name = metadata["endpoints"][_host_id]["stacks"][_stacks_id]
            shutil.move(
                src=f"{path}/{_stacks_id}", dst=f"{path}/{_host_name}/{_stacks_name}"
            )
            compose_folders.remove(str(_stacks_id))

    if len(compose_folders) > 0:
        create_directory(path=f"{path}/orphaned")
        # Create a directory structure for each orphaned stack
        for _stacks_id in compose_folders:
            shutil.move(src=f"{path}/{_stacks_id}", dst=f"{path}/orphaned/{_stacks_id}")
        metadata["endpoints"][-1] = {"name": "orphaned", "stacks": compose_folders}

    # Convert metadata to JSON and save it
    with open(f"{path}/metadata.json", "w", encoding="utf-8") as json_file:
        json.dump(metadata, json_file, indent=4)


def backup_portainer_scripts(src, project_directory, metadata):
    """
    Backup all docker compose scripts created within Portainer.
    Copies all files from src to a project directory in a folder
        of the format: current year/current month/current date.
    Also commits and pushes the changes to GIT.
    """

    dest = generate_dest_path(project_directory)

    # Copy files
    logging.info("Successfully copied files from %s to %s", src, dest)
    copy_files(src, dest, mode=2)

    # Use metadata to create a directory structure
    process_backed_up_files(metadata=metadata, path=dest)

    # Trigger encrypted backup of the .env files
    env2db.backup()

    # GIT commit and push
    timestamp = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    commit_message = f"Backup operation - `{timestamp}`"
    git_commit_push(project_directory, commit_message)


def get_metadata_from_json(cache_path):
    """
    Read metadata from the Portainer BoltDB exported as JSON.
    """
    with open(
        f"{cache_path}/portainer_data.json", "r", encoding="utf-8"
    ) as json_file:
        metadata_tmp = json.load(json_file)

    metadata = defaultdict(dict)

    # Load endpoints information
    for each_meta in metadata_tmp["endpoints"]:
        _host_id = each_meta["Value"]["Id"]
        _host_name = each_meta["Value"]["Name"]
        metadata["endpoints"][_host_id] = {
            "name": _host_name,
            "stacks": {},
        }

    # Load stacks information and map to endpoints
    for each_meta in metadata_tmp["stacks"]:
        _stacks_id = each_meta["Value"]["Id"]
        _stacks_name = each_meta["Value"]["Name"]
        _host_id = each_meta["Value"]["EndpointId"]
        metadata["endpoints"][_host_id]["stacks"][_stacks_id] = _stacks_name

    return metadata


def portainer_read_db_metadata(project_directory, db_path):
    """
    Read metadata from the Portainer BoltDB database.
    Database file locked when Portainer is running.
    So portainer is automatically stopped and started.
    """
    # Create cache directory if it does not exist
    cache_path = f"{project_directory}/.cache"
    create_directory(path=cache_path)

    # Copy database file to cache directory
    shutil.copyfile(db_path, f"{cache_path}/portainer.db")

    # * I built a small Golang docker image for this, since there's not a
    # *     reliable python client for BoltDB
    # Export metadata from Portainer BoltDB database
    logging.info("Exporting metadata from Portainer BoltDB database.")
    execute_cmd(
        cmd=f"cd {project_directory}/db-exporter \
            && docker-compose --no-ansi up --no-color \
            && docker-compose down"
    )

    # Process metadata
    metadata = get_metadata_from_json(cache_path)
    return metadata


def driver():
    """Driver function."""
    # global logging
    project_directory = get_current_module_path()
    backup_path = generate_dest_path(project_directory)
    create_directory(path=backup_path)
    # ! Logging is not working properly when running as a cron job
    # log_path = f'{ backup_path }/backup.log'
    # print(f"Log path: { log_path }")
    # logging.basicConfig(
    #      filename=log_path,
    #      level=logging.DEBUG
    # )
    logging.info("\n\n%s Starting backup operation %s", "=" * 30, "=" * 30)
    logging.info("Project directory: %s", project_directory)
    portainer_path = "/var/lib/docker/volumes/portainer_data/_data"
    compose_path = f"{portainer_path}/compose/"
    db_path = f"{portainer_path}/portainer.db"
    metadata = portainer_read_db_metadata(
        project_directory=project_directory, db_path=db_path
    )
    backup_portainer_scripts(
        src=compose_path, project_directory=project_directory, metadata=metadata
    )


if __name__ == "__main__":
    driver()
