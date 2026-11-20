import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from hexxle.check import check_puzzle
from hexxle.config import CONFIG_PATH, load_config
from hexxle.core.board import PuzzleError
from hexxle.core.paths import find_words
from hexxle.core.puzzle import parse_board_only
from hexxle.dictionary import load_dictionary
from hexxle.errors import HexxleError
from hexxle.site import serve

# Errors in the user's input or setup: reported in one line, while any
# other exception is a bug and keeps its traceback.
USER_ERRORS = (HexxleError, OSError, PuzzleError, UnicodeDecodeError)


@dataclass(frozen=True)
class Context:
    """What the commands use besides their arguments."""

    config_path: Path

    def config(self) -> dict:
        return load_config(self.config_path)


def main(
    argv: list[str] | None = None,
    config_path: Path = CONFIG_PATH,
) -> int:
    args = build_parser().parse_args(argv)
    context = Context(config_path)
    try:
        return args.handler(args, context)
    except USER_ERRORS as error:
        _print_error(error)
        return 1


def build_parser() -> argparse.ArgumentParser:
    dictionary_option = argparse.ArgumentParser(add_help=False)
    dictionary_option.add_argument(
        '-d', '--dictionary', type=Path, metavar='DICT',
        help='word list (default: from hexxle.toml)')

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

    for name, text, handler in (
        ('solve', 'list every dictionary word on a board', run_solve),
        ('check', 'validate a finished puzzle file', run_check),
    ):
        sub = commands.add_parser(
            name, help=text, parents=[dictionary_option])
        sub.add_argument('puzzle', type=Path, metavar='PUZZLE')
        sub.set_defaults(handler=handler)
    return parser


def run_serve(args: argparse.Namespace, context: Context) -> int:
    serve(args.puzzles, args.host, args.port)
    return 0


def run_solve(args: argparse.Namespace, context: Context) -> int:
    dictionary = _dictionary(args, context)
    board = parse_board_only(args.puzzle.read_text(encoding='utf-8'))
    words = find_words(board, dictionary)
    print(board.render())
    print()
    print('---')
    groups = {}
    for word in words:
        groups.setdefault(len(word), []).append(word)
    print('\n\n'.join('\n'.join(sorted(groups[length]))
                      for length in sorted(groups)))
    return 0


def run_check(args: argparse.Namespace, context: Context) -> int:
    errors, warnings = check_puzzle(args.puzzle, _dictionary(args, context))
    for message in errors:
        _print_error(message)
    _print_warnings(warnings)
    return 1 if errors else 0


def _dictionary(args: argparse.Namespace, context: Context) -> set[str]:
    """The ``-d`` word list, or else the one in the settings file.

    A relative path in the settings file is relative to that file.
    """
    path = args.dictionary
    if path is None:
        path = context.config_path.parent / context.config()['dictionary']
    return load_dictionary(path)


def _print_error(message: object) -> None:
    print('error: %s' % message, file=sys.stderr)


def _print_warnings(warnings: list[str]) -> None:
    for message in warnings:
        print('warning: %s' % message, file=sys.stderr)
