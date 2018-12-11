'''Your NYC-DB buddy.

Usage:
  bud.py machine:aws-create
  bud.py machine:rm
  bud.py hello-world
  bud.py build-image
  bud.py db:start
  bud.py db:stop
  bud.py db:wipe
  bud.py db:hello-world
  bud.py populate [--use-test-data]
  bud.py populate:status
  bud.py (-h | --help)

Options:
  -h --help       Show this screen.

Environment variables:
  NYCDB_DOCKER_MACHINE_NAME    The Docker Machine name to use (optional).
'''

from typing import Optional, List
import os
import sys
import docopt
import docker

from . import machine, image, postgres, populate, docker_util


def hello_world(client: docker.DockerClient, image: str) -> None:
    result = docker_util.run_and_remove(client, image, "echo hello world")
    print(f"The container says: {result}")


def ensure_name(name: str):
    if not name:
        sys.stderr.write("Please set NYCDB_DOCKER_MACHINE_NAME first.\n")
        sys.exit(1)


def main(argv: Optional[List[str]]=None) -> None:
    args = docopt.docopt(__doc__, argv=argv)
    name: str = os.environ.get('NYCDB_DOCKER_MACHINE_NAME', '')
    if name:
        print(f"Using the Docker Machine '{name}'.")
    if args['machine:aws-create']:
        ensure_name(name)
        machine.aws_create(name)
    elif args['machine:rm']:
        ensure_name(name)
        machine.rm(name)
    else:
        client = machine.get_client(name) if name else docker.client.from_env()
        if args['hello-world']:
            hello_world(client, 'alpine:latest')
        elif args['build-image']:
            image_id = image.build(client)
            print("Testing image...")
            hello_world(client, image_id)
            print("Image is good!")
        elif args['db:start']:
            postgres.start(client)
        elif args['db:stop']:
            postgres.stop(client)
        elif args['db:wipe']:
            postgres.wipe(client)
        elif args['db:hello-world']:
            postgres.hello_world(client)
        elif args['populate']:
            image_id = image.build(client)
            populate.populate(
                client, use_test_data=args['--use-test-data'], nycdb_image=image_id)
        elif args['populate:status']:
            populate.status(client)


if __name__ == '__main__':
    main()
