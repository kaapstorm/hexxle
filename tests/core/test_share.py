from testsweet import params, test

from hexxle.core.game import Game
from hexxle.core.puzzle import parse_puzzle
from hexxle.core.share import progress_line, share_text
from tests.core.examples import EXAMPLE

URL = 'https://example.org/hexxle/?p=2026-11-20'


def game(found=(), text=EXAMPLE):
    return Game(parse_puzzle(text), found)


ONE_REQUIRED = 'S T O P\n S\n---\nSTOP\n--- bonus\nPOTS\nTOPS\n'


@test
@params([
    (EXAMPLE, (), 'Found 0 of 2 words.'),
    (EXAMPLE, ('EXACT',), 'Found 1 of 2 words.'),
    (EXAMPLE, ('LUXE',), 'Found 0 of 2 words and 1 bonus word.'),
    (EXAMPLE, ('EXACT', 'TAXI'), 'Puzzle completed! Found 2 words.'),
    (EXAMPLE, ('EXACT', 'TAXI', 'LUXE'),
     'Puzzle completed! Found 2 words and 1 bonus word.'),
    (ONE_REQUIRED, (), 'Found 0 of 1 word.'),
    (ONE_REQUIRED, ('STOP', 'POTS', 'TOPS'),
     'Puzzle completed! Found 1 word and 2 bonus words.'),
])
def describes_progress(text, found, line):
    assert progress_line(game(found, text)) == line


@test
def shares_the_puzzle_progress_and_link():
    assert share_text('2026-11-20', game(('EXACT',)), URL) == (
        'Hexxle · 20 Nov 2026\n'
        'Found 1 of 2 words.\n'
        + URL)


@test
def names_a_labelled_puzzle():
    text = share_text('2026-11-18_quick_one', game(), URL)
    assert text.split('\n')[0] == 'Hexxle · 18 Nov 2026 · quick one'


@test
def never_includes_a_word():
    text = share_text('2026-11-20', game(('EXACT', 'TAXI', 'LUXE')), URL)
    for word in ('EXACT', 'TAXI', 'LUXE'):
        assert word not in text.upper()
