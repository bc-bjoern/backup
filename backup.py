#!/usr/bin/env python3

import subprocess
import os
import json
import datetime

def run_rsync(source, destination, server, port, username, authentication_method, password=None, excludes=None, use_sudo=False, role_folder="", schedule_type="daily"):
    # Run rsync command
    rsync_command = ["rsync", "-av", "--delete"]

    if excludes:
        for exclude_pattern in excludes:
            rsync_command.extend(["--exclude", exclude_pattern])

    # Build local destination based on the provided schedule_type
    if schedule_type == "daily":
        parent_folder = datetime.datetime.now().strftime('%d')
    elif schedule_type == "monthly":
        parent_folder = datetime.datetime.now().strftime('%m')
    else:
        parent_folder = ""

    local_destination = os.path.join(destination, role_folder, schedule_type, parent_folder)
    os.makedirs(local_destination, exist_ok=True)

    if use_sudo:
        rsync_command.append("--rsync-path=sudo rsync")

        if excludes:
            for exclude_pattern in excludes:
                rsync_command.extend(["--exclude", exclude_pattern])

        rsync_command.extend(["-e", f"ssh -p {port}", f"{username}@{server}:{source}", local_destination])
    else:
        if authentication_method == 'ssh_key':
            rsync_command.extend(["-e", f"ssh -i {password} -p {port}", f"{username}@{server}:{source}", local_destination])
        else:
            rsync_command.extend(["-e", f"ssh -p {port}", f"{username}@{server}:{source}", local_destination])

    # Run the rsync command using subprocess without setting RSYNC_PASSWORD
    subprocess.run(rsync_command)

    # Unset RSYNC_PASSWORD environment variable after rsync command
    os.environ.pop("RSYNC_PASSWORD", None)

def backup_servers(server_configurations, destination):
    # Set the working directory to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Backup each server based on its configuration
    for role, config in server_configurations.items():
        if config["enabled"]:
            role_folder = role.lower()

            if config["authentication_method"] == 'ssh_key':
                private_key = config["ssh_key_path"]
            else:
                private_key = config["password"]

            for schedule_type in ["daily", "monthly"]:
                if config["schedule"][schedule_type]:
                    print(f"Run {role} {schedule_type}:\n")
                    run_rsync(config["source"], destination, config["server"], config["port"], config["username"],
                              config["authentication_method"], password=private_key, excludes=config.get("excludes", []),
                              use_sudo=config.get("use_sudo", False), role_folder=role_folder, schedule_type=schedule_type)
        else:
            print(f"Backup for {role} is disabled.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Load server configurations from JSON file
    with open("/backup/config.json", "r") as config_file:
        server_configurations = json.load(config_file)

    # destination = os.environ.get("BACKUP_DESTINATION")
    destination = '/backup'
    backup_servers(server_configurations, destination)
