from testsweet import params, test

from hexxle.core.puzzle import parse_puzzle
from hexxle.core.trace import Trace
from tests.core.examples import EXAMPLE


def started(*positions):
    trace = Trace(parse_puzzle(EXAMPLE).board)
    trace.start(positions[0])
    for pos in positions[1:]:
        trace.move_to(pos)
    return trace


T, A, C, X, N = (1, 0), (3, 0), (2, 1), (4, 1), (6, 3)


@test
@params([
    ([T, A], X, True, 'TAX'),       # a neighbour extends the trace
    ([T], N, False, 'T'),           # not a neighbour
    ([T, A, X], A, True, 'TA'),     # back one tile removes a letter
    ([T, A, C], T, False, 'TAC'),   # already used, and not the last tile
])
def moves_to_a_tile(path, pos, expected_changed, expected_word):
    trace = started(*path)
    changed = trace.move_to(pos)
    word = trace.word()
    assert (changed, word) == (expected_changed, expected_word)


@test
def finish_returns_the_word_and_clears():
    trace = started((1, 0), (3, 0))
    result = (trace.finish(), trace.path, trace.finish())
    assert result == ('TA', [], None)


@test
def finish_while_armed_returns_nothing_and_disarms():
    trace = started((1, 0), (3, 0))
    trace.set_armed(True)
    result = (trace.finish(), trace.path, trace.armed)
    assert result == (None, [], False)


@test
def moving_before_starting_does_nothing():
    trace = Trace(parse_puzzle(EXAMPLE).board)
    changed = trace.move_to((1, 0))
    assert changed is False
