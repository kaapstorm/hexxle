from testsweet import params, test

from hexxle.core.index import (
    INDEX_NAME,
    PUZZLES_DIR,
    file_name_of,
    identifier_of,
    is_identifier,
    make_index,
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
