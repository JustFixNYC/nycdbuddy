import os
import sys
from typing import List
import subprocess


def run_docker_machine(args: List[str]):
    try:
        subprocess.check_call(['docker-machine'] + args)
    except subprocess.CalledProcessError:
        # The output was piped directly to stdout/stderr, so the user
        # should see it. Let's not bother confusing them with a
        # traceback.
        sys.exit(1)


def aws_create(name: str):
    # https://docs.docker.com/machine/drivers/aws/#environment-variables
    os.environ.setdefault('AWS_INSTANCE_TYPE', 't2.large')
    os.environ.setdefault('AWS_SECURITY_GROUP', 'nycdbuddy')

    # Note that the AWS keys should be defined either in the environment
    # or the AWS credentials file thingy that docker-machine supports.

    print(f"Creating Docker machine '{name}'.")

    run_docker_machine(['create', name, '--driver=amazonec2'])


def rm(name: str):
    print(f"Removing Docker machine '{name}'.")

    run_docker_machine(['rm', name])
