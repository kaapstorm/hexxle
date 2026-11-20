from testsweet import catch_exceptions, params, test

from hexxle.core.index import (
    INDEX_NAME,
    PUZZLES_DIR,
    choose,
    dump_index,
    file_name_of,
    identifier_of,
    is_identifier,
    make_index,
    parse_index,
)


@test
@params([
    ('2026-11-20', True),
    ('2026-11-20_express', True),
    ('2026-11-20.txt', False),
    ('../index', False),
    ('', False),
    (20261120, False),
    (None, False),
])
def recognises_identifiers(value, expected):
    result = is_identifier(value)
    assert result == expected


@test
@params([
    ('["2026-11-20", "2026-11-18_express"]',
     ['2026-11-20', '2026-11-18_express']),
    ('[]', []),
    ('[1, 2, 3]', []),
    ('["2026-11-20", "../x", null, "2026-11-19"]',
     ['2026-11-20', '2026-11-19']),
])
def parses_an_index_dropping_bad_entries(text, expected):
    index = parse_index(text)
    assert index == expected


@test
@params([('not json',), ('["2026-11-20"',), ('{"a": 1}',), ('"x"',), ('',)])
def rejects_an_index_that_is_not_a_json_list(text):
    with catch_exceptions() as excs:
        parse_index(text)
    kinds = [type(e) for e in excs]
    assert kinds == [ValueError]


INDEX = ['2026-11-20', '2026-11-18_express']


@test
@params([
    (None, '2026-11-20'),
    ('2026-11-18_express', '2026-11-18_express'),
    ('2020-01-01', None),
    ('../index', None),
    ('', None),
])
def chooses_the_puzzle_to_play(requested, expected):
    chosen = choose(INDEX, requested)
    assert chosen == expected


@test
def names_the_site_layout():
    layout = (PUZZLES_DIR, INDEX_NAME, file_name_of('2026-11-20_express'))
    assert layout == ('puzzles', 'index.json', '2026-11-20_express.txt')


@test
@params([
    ('2026-11-20.txt', '2026-11-20'),
    ('2026-11-20_express.txt', '2026-11-20_express'),
    ('2026-11-20.md', None),
    ('2026-11-20', None),
    ('notes.txt', None),
    ('index.json', None),
    ('.txt', None),
])
def finds_the_identifier_of_a_file_name(name, expected):
    ident = identifier_of(name)
    assert ident == expected


@test
def index_keeps_valid_puzzles_newest_first():
    names = ['2026-11-18.txt', 'index.json', '2026-11-20_weekly.txt',
             '2026-11-20_express.txt', '2026-11-20.txt', 'notes.txt',
             '2026-11-19.md']
    index = make_index(names)
    assert index == ['2026-11-20', '2026-11-20_express',
                     '2026-11-20_weekly', '2026-11-18']


@test
def a_dumped_index_reads_back():
    index = ['2026-11-20', '2026-11-18_express']
    text = dump_index(index)
    assert text.endswith('\n')
    assert parse_index(text) == index
