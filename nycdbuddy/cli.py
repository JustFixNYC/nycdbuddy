'''Your NYC-DB buddy.

Usage:
  bud.py machine:aws-create [--name=<name>]
  bud.py machine:rm [--name=<name>]
  bud.py (-h | --help)

Options:
  -h --help       Show this screen.
  --name=<name>   docker-machine name to use [default: nycdbuddy].
'''

from typing import Optional, List
import docopt

from . import machine


def main(argv: Optional[List[str]]=None) -> None:
    args = docopt.docopt(__doc__, argv=argv)
    name: str = args['--name']
    if args['machine:aws-create']:
        machine.aws_create(name)
    elif args['machine:rm']:
        machine.rm(name)


if __name__ == '__main__':
    main()
