import os
import sys
import json
from typing import List
import subprocess
import docker


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
    os.environ.setdefault('AWS_INSTANCE_TYPE', 't2.xlarge')

    # Note that we originally set the AWS_SECURITY_GROUP here too, but
    # docker-machine seemed to ignore it, and when we passed it explicitly
    # as a command-line option, it failed with the following error:
    #
    # > Missing instance ID, this is likely due to a failure during machine creation
    # > Error creating machine: Error in driver during machine creation:
    # > InvalidGroup.Duplicate: The security group 'nycdbuddy' already exists
    # > for VPC 'vpc-5844af3c' status code: 400,
    # > request id: 9c71c004-cb2d-4e64-bd36-179a6d5a3790
    #
    # So I guess we won't set the security group, then.

    # Note that the AWS keys should be defined either in the environment
    # or the AWS credentials file thingy that docker-machine supports.

    print(f"Creating Docker Machine '{name}'.")

    run_docker_machine(['create', name, '--driver=amazonec2'])


def rm(name: str):
    print(f"Removing Docker Machine '{name}'.")

    run_docker_machine(['rm', name])


def get_client(name: str) -> docker.DockerClient:
    info_bytes = subprocess.check_output(['docker-machine', 'inspect', name])

    info = json.loads(info_bytes, encoding="utf-8")

    cert_path = info['HostOptions']['AuthOptions']['StorePath']

    ip = info['Driver']['IPAddress']
    ip_url = f"tcp://{ip}:2376"

    env = {
        'DOCKER_HOST': ip_url,
        'DOCKER_TLS_VERIFY': '1',
        'DOCKER_CERT_PATH': cert_path,
        'DOCKER_MACHINE_NAME': name
    }

    client = docker.client.from_env(environment=env)

    return client
