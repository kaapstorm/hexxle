from testsweet import params, test

from hexxle.core.game import (
    ALREADY, BONUS, FOUND, NOT_A_WORD, SINGLE_LETTER, TOO_SHORT, Game)
from hexxle.core.puzzle import parse_puzzle
from tests.core.examples import EXAMPLE


def game(found=()):
    return Game(parse_puzzle(EXAMPLE), found)


def two_s(words):
    text = 'S T O P\n S\n---\n' + '\n'.join(words) + '\n'
    return Game(parse_puzzle(text))


@test
def classifies_each_submission():
    g = game()
    outcomes = [g.submit(w) for w in
                ['T', 'TA', 'TAX', 'EXACT', 'EXACT', 'LUXE', 'LUXE',
                 'ACED']]
    assert outcomes == [SINGLE_LETTER, TOO_SHORT, TOO_SHORT, FOUND,
                        ALREADY, BONUS, ALREADY, NOT_A_WORD]


@test
def tracks_progress_and_completion():
    g = game()
    g.submit('EXACT')
    g.submit('LUXE')
    before = (g.progress(), g.is_complete())
    g.submit('TAXI')
    after = (g.progress(), g.is_complete())
    assert before == ((1, 2, 1), False)
    assert after == ((2, 2, 1), True)


@test
def lists_found_words():
    g = game(['TAXI', 'LUXE', 'EXACT'])
    lists = (g.found_groups(), g.found_bonus(), g.found_words())
    assert lists == ([(4, ['TAXI']), (5, ['EXACT'])], ['LUXE'],
                     ['EXACT', 'LUXE', 'TAXI'])


@test
def drops_saved_words_that_left_the_puzzle():
    words = game(['EXACT', 'GONE']).found_words()
    assert words == ['EXACT']


@test
@params([
    ((1, 0), (1, 2)),   # T: TAXI starts; TAXI and EXACT use it
    ((3, 2), (1, 1)),   # E: EXACT starts and uses it
    ((5, 2), (0, 1)),   # I: TAXI uses it
    ((6, 1), (0, 0)),   # L: only the bonus word LUXE
])
def counts_hints(pos, expected):
    hints = game().hints(pos)
    assert hints == expected


@test
def bonus_only_tiles_start_dimmed_and_found_words_dim_tiles():
    g = game()
    before = (g.is_dimmed((6, 1)), g.is_dimmed((5, 2)))
    g.submit('TAXI')
    after = (g.hints((5, 2)), g.is_dimmed((5, 2)), g.hints((1, 0)))
    assert before == (True, False)
    assert after == ((0, 0), True, (0, 1))


@test
def a_word_with_two_paths_counts_on_every_tile_it_could_use():
    g = two_s(['STOP', 'POTS'])
    before = [g.hints(p) for p in [(0, 0), (1, 1), (2, 0), (6, 0)]]
    g.submit('STOP')
    after = [g.hints(p) for p in [(0, 0), (1, 1), (2, 0), (6, 0)]]
    assert before == [(1, 2), (1, 2), (0, 2), (1, 2)]
    assert after == [(0, 1), (0, 1), (0, 1), (1, 1)]


@test
def a_word_listed_twice_or_in_both_lists_counts_once_as_required():
    text = 'S T O P\n S\n---\nSTOP\nSTOP\n--- bonus\nSTOP\n'
    g = Game(parse_puzzle(text), ['STOP', 'STOP'])
    result = (g.progress(), g.submit('STOP'), g.found_bonus())
    assert result == ((1, 1, 0), ALREADY, [])
