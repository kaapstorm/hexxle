from testsweet import test

from tests.core.examples import EXAMPLE
from tests.fixture_paths import EXAMPLE_PATH


@test
def the_example_fixture_file_is_the_example_puzzle():
    text = EXAMPLE_PATH.read_text(encoding='utf-8')
    assert text == EXAMPLE
