'''Your NYC-DB buddy.

Usage:
  bud.py machine:aws-create [--name=<name>]
  bud.py machine:rm [--name=<name>]
  bud.py machine:hello-world [--name=<name>]
  bud.py hello-world
  bud.py (-h | --help)

Options:
  -h --help       Show this screen.
  --name=<name>   docker-machine name to use [default: nycdbuddy].
'''

from typing import Optional, List
import docopt
import docker
import random

from . import machine


def hello_world(client: docker.DockerClient) -> None:
    cname = f"hello-world-{random.random()}"
    result = client.containers.run("alpine:latest", "echo hello world", name=cname)

    print(f"The container says: {result}")

    print("Removing container.")

    client.containers.get(cname).remove()


def main(argv: Optional[List[str]]=None) -> None:
    args = docopt.docopt(__doc__, argv=argv)
    name: str = args['--name']
    if args['machine:aws-create']:
        machine.aws_create(name)
    elif args['machine:rm']:
        machine.rm(name)
    elif args['machine:hello-world']:
        client = machine.get_client(name)
        hello_world(client)
    elif args['hello-world']:
        hello_world(docker.client.from_env())
    else:
        raise AssertionError('we should never reach this point!')


if __name__ == '__main__':
    main()
