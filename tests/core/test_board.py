from testsweet import catch_exceptions, params, test

from hexxle.core.board import PuzzleError, parse_board
from tests.core.examples import EXAMPLE, TILE_COUNT

BOARD_LINES = EXAMPLE.split('\n')[:4]


@test
def letters_sit_at_text_column_and_row():
    board = parse_board(BOARD_LINES)
    letters = [board.letter(p) for p in [(1, 0), (0, 1), (6, 3)]]
    assert letters == ['T', 'S', 'N']


@test
def interior_tile_has_six_neighbours():
    found = parse_board(BOARD_LINES).neighbours((2, 1))
    assert found == [(0, 1), (1, 0), (1, 2), (3, 0), (3, 2), (4, 1)]


@test
def corner_tile_has_three_neighbours():
    found = parse_board(BOARD_LINES).neighbours((1, 0))
    assert found == [(0, 1), (2, 1), (3, 0)]


@test
def positions_are_sorted_by_row_then_column():
    board = parse_board(BOARD_LINES)
    found = board.positions()
    assert found[:4] == [(1, 0), (3, 0), (5, 0), (0, 1)]
    assert len(found) == TILE_COUNT
    assert (1, 0) in board
    assert (0, 0) not in board


@test
@params([
    (['a b', ' c'], 'A B\n C'),            # lower case
    (['', 'A B', ' C', ''], 'A B\n C'),    # blank lines around
    (['  A B', '   C'], 'A B\n C'),        # indented: shifted left
    (['A B   ', ' C\r'], 'A B\n C'),       # trailing space, CR
    (['A _ B', ' C'], 'A   B\n C'),        # explicit gap
    ([' A B', 'C'], ' A B\nC'),            # odd parity first
])
def renders_canonically(lines, expected):
    rendered = parse_board(lines).render()
    assert rendered == expected


@test
@params([
    (['A B', 'C'], 2, 1),        # adjacent rows share parity
    (['A  B'], 1, 4),            # mixed parity within a row
    (['A B', '', ' C'], 2, None),  # blank line between rows
    (['A\tB'], 1, 2),            # tab
    (['A 3'], 1, 3),             # not a letter
    (['A B', ' C  _'], 2, 5),    # gap off the lattice
    (['A \u00df'], 1, 3),         # non-ASCII letter
    ([], None, None),            # no tiles
])
def rejects_malformed_boards(lines, line, column):
    with catch_exceptions() as excs:
        parse_board(lines)
    error = excs[0]
    position = (error.line, error.column)
    assert type(error) is PuzzleError
    assert position == (line, column)


@test
def error_message_includes_position():
    with catch_exceptions() as excs:
        parse_board(['A 3'], first_line=10)
    message = str(excs[0])
    assert message.startswith('line 10, column 3: ')
