import argparse
import sys
from pathlib import Path

from hexxle.errors import HexxleError
from hexxle.site import serve

# Errors in the user's input or setup: reported in one line, while any
# other exception is a bug and keeps its traceback.
USER_ERRORS = (HexxleError, OSError)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except USER_ERRORS as error:
        _print_error(error)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='hexxle')
    commands = parser.add_subparsers(dest='command', required=True)

    serve_parser = commands.add_parser(
        'serve', help='build the site and serve it locally')
    serve_parser.add_argument(
        '--puzzles', type=Path, default=Path('puzzles'), metavar='DIR',
        help='directory of puzzle files (default: puzzles)')
    serve_parser.add_argument(
        '--host', default='127.0.0.1',
        help='address to listen on (default: 127.0.0.1)')
    serve_parser.add_argument(
        '--port', type=int, default=8000,
        help='port to listen on (default: 8000)')
    serve_parser.set_defaults(handler=run_serve)
    return parser


def run_serve(args: argparse.Namespace) -> int:
    serve(args.puzzles, args.host, args.port)
    return 0


def _print_error(message: object) -> None:
    print('error: %s' % message, file=sys.stderr)
