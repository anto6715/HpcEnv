#!/usr/bin/env python
import getpass
import glob
import os
import subprocess
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from typing import List, Optional

########################
#
# VARIABLES
#
########################
DEFAULT_CHECKPOINT = Path(__file__).parent / "checkpoint"
EMAIL_ADDRESSES = ["antonio.mariani@cmcc.it"]
EMAIL_SENDER = "scc-noreply@cmcc.it"


########################
#
# FUNCTIONS
#
########################
def get_args(raw_args=None) -> Namespace:
    import argparse

    parse = argparse.ArgumentParser(description="Restart cleaning")
    # General args
    parse.add_argument(
        "experiment_dir", type=Path, help="Directory where experiments is running"
    )
    parse.add_argument(
        "-c",
        "--checkpoint",
        type=Path,
        default=DEFAULT_CHECKPOINT,
        help="Checkpoint file",
    )

    return parse.parse_args(raw_args)


def find_latest_model_dir(base_path: Path) -> Optional[Path]:
    # Get a list of all directories named 'model' in the subdirectories
    nemos = glob.glob(os.path.join(base_path, "*/model/nemo"))

    # If no directories are found, return None
    if not nemos:
        return None

    # Get the modification time for each directory
    dirs_with_mtime = [(n, os.lstat(n).st_mtime) for n in nemos]

    # Sort directories by modification time (newest first)
    latest_nemo = max(dirs_with_mtime, key=lambda x: x[1])[0]

    return Path(latest_nemo).parent


def is_in_file(str_to_check: str, file_path: Path) -> bool:
    with open(file_path, "r") as file:
        lines = file.read().splitlines()

    for line in lines:
        if str_to_check in line:
            return True

    return False


def send_alert(experiment_dir: Path, latest_nemo_dir: Path, stuck: bool, started: bool):
    # Usage example
    subject = "RUN MONITORING"
    body = f"""
Monitoring report: 
    - Stuck: {stuck}
    - Started: {started}
    - User: {getpass.getuser()}
    - Experiment dir: {experiment_dir}
    - Latest NEMO dir: {latest_nemo_dir}

This email is automatically generated, any response to it will be ignored
    """
    to_email = ", ".join(EMAIL_ADDRESSES)
    from_email = EMAIL_SENDER

    print(body)
    send_email(subject, body, to_email, from_email)


def send_email(subject, body, to_email, from_email):
    try:
        # Prepare the mail command
        mail_command = ["mail", "-s", subject, "-r", from_email, to_email]

        # Open a subprocess to execute the mail command
        process = subprocess.Popen(
            mail_command,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        # Send the email body to the mail command
        stdout, stderr = process.communicate(input=body.encode("utf-8"))

        if process.returncode == 0:
            print("Email sent successfully!")
        else:
            print(f"Failed to send email. Error: {stderr.decode('utf-8')}")
    except Exception as e:
        print(f"An error occurred: {e}")


def main(raw_args: List["str"] = None):
    args = get_args(raw_args)
    experiment_dir: Path = args.experiment_dir
    checkpoint: Path = args.checkpoint

    ########################
    # CHECK INPUTS
    ########################
    if not experiment_dir.is_dir():
        raise NotADirectoryError()
    checkpoint.touch(exist_ok=True)

    latest_nemo_dir = find_latest_model_dir(experiment_dir)
    if latest_nemo_dir is None:
        run_started = False
        run_stuck = True
    else:
        run_started = True
        run_stuck = is_in_file(latest_nemo_dir.as_posix(), checkpoint)

    ########################
    # UPDATE CHECKPOINT
    ########################
    if run_started:
        with checkpoint.open(mode="a") as f:
            timestamp = datetime.now().strftime("%Y%m%dT%H:%M:%S")
            new_str = f"[{timestamp}] - {latest_nemo_dir.as_posix()}\n"
            f.write(new_str)

    ########################
    # ALERTING
    ########################
    if run_stuck or not run_started:
        send_alert(experiment_dir, latest_nemo_dir, run_stuck, run_started)


if __name__ == "__main__":
    main()
