from testsweet import test

from hexxle.core.puzzle import parse_puzzle
from hexxle.core.trace import Trace
from tests.core.examples import EXAMPLE


def started(*positions):
    trace = Trace(parse_puzzle(EXAMPLE).board)
    trace.start(positions[0])
    for pos in positions[1:]:
        trace.move_to(pos)
    return trace


@test
def extends_through_neighbours():
    word = started((1, 0), (3, 0), (4, 1)).word()
    assert word == 'TAX'


@test
def ignores_a_tile_that_is_not_a_neighbour():
    trace = started((1, 0))
    changed = trace.move_to((6, 3))
    word = trace.word()
    assert (changed, word) == (False, 'T')


@test
def moving_back_one_tile_removes_the_last_letter():
    trace = started((1, 0), (3, 0), (4, 1))
    changed = trace.move_to((3, 0))
    word = trace.word()
    assert (changed, word) == (True, 'TA')


@test
def ignores_an_already_used_tile():
    trace = started((1, 0), (3, 0), (2, 1))
    changed = trace.move_to((1, 0))
    word = trace.word()
    assert (changed, word) == (False, 'TAC')


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
