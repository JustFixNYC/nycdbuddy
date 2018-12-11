'''Your NYC-DB buddy.

Usage:
  bud.py machine:aws-create [--name=<name>]
  bud.py machine:rm [--name=<name>]
  bud.py hello-world [--name=<name>] [--no-machine]
  bud.py build-image [--name=<name>] [--no-machine]
  bud.py start-db [--name=<name>] [--no-machine]
  bud.py stop-db [--name=<name>] [--no-machine]
  bud.py hello-db [--name=<name>] [--no-machine]
  bud.py (-h | --help)

Options:
  -h --help       Show this screen.
  --name=<name>   Docker Machine name to use [default: nycdbuddy].
  --no-machine    Don't use any Docker Machine.
'''

from typing import Optional, List
import docopt
import docker
import random

from . import machine, image, postgres


def hello_world(client: docker.DockerClient, image: str) -> None:
    cname = f"hello-world-{random.random()}"
    result = client.containers.run(image, "echo hello world", name=cname)

    print(f"The container says: {result}")

    print("Removing container.")

    client.containers.get(cname).remove()


def main(argv: Optional[List[str]]=None) -> None:
    args = docopt.docopt(__doc__, argv=argv)
    name: str = args['--name']
    no_machine: bool = args['--no-machine']
    if args['machine:aws-create']:
        machine.aws_create(name)
    elif args['machine:rm']:
        machine.rm(name)
    else:
        client = docker.client.from_env() if no_machine else machine.get_client(name)
        if args['hello-world']:
            hello_world(client, 'alpine:latest')
        elif args['build-image']:
            image_id = image.build(client)
            print("Testing image...")
            hello_world(client, image_id)
            print("Image is good!")
        elif args['start-db']:
            postgres.start(client)
        elif args['stop-db']:
            postgres.stop(client)
        elif args['hello-db']:
            postgres.hello_world(client)


if __name__ == '__main__':
    main()
