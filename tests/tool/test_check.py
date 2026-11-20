import tempfile
from pathlib import Path

from testsweet import params, test

from hexxle.check import check_puzzle
from hexxle.dictionary import load_dictionary
from tests.core.examples import EXAMPLE
from tests.fixture_paths import EXAMPLE_PATH, WORDS_PATH

WORDS = load_dictionary(WORDS_PATH)


@test
def example_passes_with_pruned_words_as_warnings():
    errors, warnings = check_puzzle(EXAMPLE_PATH, WORDS)
    pruned = sorted(w for w in ['ACED', 'AXED']
                    if any(w in line for line in warnings))
    assert errors == []
    assert pruned == ['ACED', 'AXED']
    assert len(warnings) == 2


@test
def warns_about_listed_words_missing_from_the_dictionary():
    errors, warnings = check_puzzle(EXAMPLE_PATH, WORDS - {'LUXE'})
    mentioning = [line for line in warnings if 'LUXE' in line]
    assert errors == []
    assert len(mentioning) == 1


@test
@params([
    ('puzzle.txt', EXAMPLE, 'puzzle.txt'),
    ('2026-11-20.md', EXAMPLE, '2026-11-20.md'),
    ('2026-11-20.txt', EXAMPLE.replace('TAXI', 'TAXIS'), 'TAXIS'),
    ('2026-11-20.txt', 'A B\nC\n---\nABCD\n', 'line 2'),
])
def reports_errors(name, text, expected_text):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(text)
        errors, warnings = check_puzzle(path, WORDS)
    assert len(errors) == 1
    assert expected_text in errors[0]
