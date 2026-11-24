from testsweet import catch_exceptions, params, test

from hexxle.core.board import PuzzleError
from hexxle.core.puzzle import (
    describe_identifier,
    parse_identifier,
    parse_puzzle,
    puzzle_errors,
)
from tests.core.examples import EXAMPLE


@test
def parses_the_example():
    puzzle = parse_puzzle(EXAMPLE)
    lists = (puzzle.required, puzzle.bonus)
    letter = puzzle.board.letter((4, 1))
    assert lists == (['EXACT', 'TAXI'], ['LUXE'])
    assert letter == 'X'


@test
@params([
    (EXAMPLE.replace('\n', '\r\n'),),
    (EXAMPLE.rstrip('\n'),),
    (EXAMPLE.replace('EXACT', 'exact  '),),
    (EXAMPLE.replace('TAXI\n', 'TAXI\n\n\n'),),
])
def tolerates_line_endings_case_and_blank_lines(text):
    puzzle = parse_puzzle(text)
    lists = (puzzle.required, puzzle.bonus)
    assert lists == (['EXACT', 'TAXI'], ['LUXE'])


@test
def reads_the_emoji_after_a_word():
    text = EXAMPLE.replace('EXACT', 'exact \U0001f327\ufe0f').replace(
        'LUXE', 'LUXE  \u2728 \U0001f48e ')
    puzzle = parse_puzzle(text)
    lists = (puzzle.required, puzzle.bonus)
    assert lists == (['EXACT', 'TAXI'], ['LUXE'])
    assert puzzle.emoji == {
        'EXACT': '\U0001f327\ufe0f', 'LUXE': '\u2728 \U0001f48e'}


@test
def most_words_have_no_emoji():
    assert parse_puzzle(EXAMPLE).emoji == {}


@test
def board_only_file_has_no_words():
    puzzle = parse_puzzle('A B\n C\n')
    lists = (puzzle.required, puzzle.bonus)
    assert lists == ([], [])


@test
@params([
    ('A B\n C\n--- extras\nABCD\n', 3),
    ('A B\n C\n---\nABCD\n---\nABCE\n', 5),
    ('A B\n C\n--- bonus\nABCD\n', 3),
    ('A B\n C\n---\nAB-CD\n', 4),
    ('A B\n C\n---\nABCD EFGH\n', 4),         # a second word, not an emoji
    ('A B\n C\n---\nABCD \u2728 x\n', 4),
    ('A B\n C\n---\n\u2728 ABCD\n', 4),        # the emoji comes second
    ('A B\nC\n---\nABCD\n', 2),
])
def rejects_malformed_files(text, line):
    with catch_exceptions() as excs:
        parse_puzzle(text)
    error_line = excs[0].line
    assert type(excs[0]) is PuzzleError
    assert error_line == line


@test
@params([
    ('---\n', 'required'),
    ('---\nTAX\nTAXI\n', 'TAX'),
    ('---\nTAXI\nTAXI\n', 'TAXI'),
    ('---\nTAXI\n--- bonus\nTAXI\n', 'TAXI'),
    ('---\nTAXI\nTAXIS\n', 'TAXIS'),
])
def reports_list_problems(sections, expected_text):
    board = '\n'.join(EXAMPLE.split('\n')[:4]) + '\n\n'
    errors = puzzle_errors(parse_puzzle(board + sections))
    matching = [e for e in errors if expected_text in e]
    assert len(matching) == 1


@test
def example_has_no_list_problems():
    errors = puzzle_errors(parse_puzzle(EXAMPLE))
    assert errors == []


@test
@params([
    ('2026-11-20', ('2026-11-20', None)),
    ('2025-07-07_express_b', ('2025-07-07', 'express_b')),
])
def parses_identifiers(ident, expected):
    parsed = parse_identifier(ident)
    assert parsed == expected


@test
@params([
    ('2026-11-20-express',), ('2026-13-01',), ('2026-11-32',),
    ('26-11-20',), ('2026-11-20_',), ('2026-11-20_Express',),
    ('../2026-11-20',), ('',),
])
def rejects_bad_identifiers(ident):
    with catch_exceptions() as excs:
        parse_identifier(ident)
    kinds = [type(e) for e in excs]
    assert kinds == [ValueError]


@test
@params([
    ('2026-11-20', ('20 Nov 2026', '')),
    ('2025-07-07_express_b', ('7 Jul 2025', 'express b')),
])
def describes_identifiers(ident, expected):
    described = describe_identifier(ident)
    assert described == expected
