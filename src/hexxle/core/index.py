"""The site's puzzles: where they live, the index, and which to play.

Puzzle ``<identifier>`` is the file ``puzzles/<identifier>.txt``. The
index, ``puzzles/index.json``, is a JSON list of identifiers, newest
first. The tool writes this layout and the game reads it.
"""

import json

from hexxle.core.puzzle import parse_identifier

PUZZLES_DIR = 'puzzles'
INDEX_NAME = 'index.json'
PUZZLE_SUFFIX = '.txt'


def is_identifier(value):
    """Whether ``value`` is a string that is a valid puzzle identifier."""
    if not isinstance(value, str):
        return False
    try:
        parse_identifier(value)
    except ValueError:
        return False
    return True


def file_name_of(ident):
    """The file name of the puzzle ``ident``."""
    return ident + PUZZLE_SUFFIX


def identifier_of(file_name):
    """The identifier ``file_name`` is the puzzle file of, or ``None``."""
    if not file_name.endswith(PUZZLE_SUFFIX):
        return None
    ident = file_name[:len(file_name) - len(PUZZLE_SUFFIX)]
    if not is_identifier(ident):
        return None
    return ident


def make_index(names):
    """The index of the puzzle files among file ``names``, newest first.

    Within one date the unlabelled puzzle comes first, then labels in
    order.
    """
    parsed = []
    for name in names:
        ident = identifier_of(name)
        if ident is not None:
            date, label = parse_identifier(ident)
            # One sort on one key: MicroPython's sort is not stable.
            newest_first = -int(date.replace('-', ''))
            parsed.append((newest_first, label or '', ident))
    parsed.sort()
    return [ident for _, _, ident in parsed]


def dump_index(index):
    """The text of ``index.json`` for the identifiers in ``index``."""
    return json.dumps(index) + '\n'


def parse_index(text):
    """The valid identifiers in the index ``text``, in its order.

    Entries that are not identifiers are dropped. Raises ``ValueError``
    if ``text`` is not a JSON list.
    """
    try:
        index = json.loads(text)
    except ValueError:
        raise ValueError('the index is not valid JSON')
    if not isinstance(index, list):
        raise ValueError('the index is not a list')
    return [ident for ident in index if is_identifier(ident)]


def choose(index, requested):
    """The identifier to play from a non-empty ``index``.

    ``requested`` is the identifier asked for, or ``None`` for the
    newest. Returns ``None`` if ``requested`` is not in the index.
    """
    if requested is None:
        return index[0]
    if is_identifier(requested) and requested in index:
        return requested
    return None
