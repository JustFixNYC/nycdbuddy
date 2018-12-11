'''Your NYC-DB buddy.

Usage:
  bud.py buildmachine
  bud.py (-h | --help)

Options:
  -h --help    Show this screen.
'''

from typing import Optional, List
import docopt


def main(argv: Optional[List[str]]=None) -> None:
    args = docopt.docopt(__doc__, argv=argv)
    if args['buildmachine']:
        raise NotImplementedError()


if __name__ == '__main__':
    main()
