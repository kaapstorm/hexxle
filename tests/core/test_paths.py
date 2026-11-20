from testsweet import params, test

from hexxle.core.board import parse_board
from hexxle.core.paths import find_paths, find_words
from hexxle.core.puzzle import parse_puzzle
from tests.core.examples import EXAMPLE, PATHS

BOARD = parse_puzzle(EXAMPLE).board
TWO_S = parse_board(['S T O P', ' S'])


@test
def finds_the_only_path():
    paths = find_paths(BOARD, 'EXACT')
    assert paths == [tuple(PATHS['EXACT'])]


@test
def finds_every_path():
    paths = find_paths(TWO_S, 'STOP')
    assert paths == [
        ((0, 0), (2, 0), (4, 0), (6, 0)),
        ((1, 1), (2, 0), (4, 0), (6, 0)),
    ]


@test
@params([('TAXIS',), ('TATA',), ('',)])
def finds_nothing_for_untraceable_words(word):
    paths = find_paths(BOARD, word)
    assert paths == []


@test
def finds_dictionary_words_on_the_board():
    words = ['EXACT', 'TAXI', 'LUXE', 'ACED', 'AXED', 'TAX', 'ZEBRA',
             'TAXIS']
    found = find_words(BOARD, words)
    assert found == {'EXACT', 'TAXI', 'LUXE', 'ACED', 'AXED'}


@test
def the_example_paths_spell_their_words():
    for word in PATHS:
        paths = find_paths(BOARD, word)
        assert tuple(PATHS[word]) in paths, word
