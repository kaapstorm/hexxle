from testsweet import test

from hexxle.dictionary import load_dictionary
from tests.fixture_paths import WORDS_PATH


@test
def keeps_only_plain_lowercase_words_of_four_or_more():
    words = load_dictionary(WORDS_PATH)
    assert words == {'EXACT', 'TAXI', 'LUXE', 'ACED', 'AXED', 'ZEBRA'}
