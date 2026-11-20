from testsweet import test

from hexxle.site import site_server
from tests.browser.support import open_page
from tests.core.examples import TILE_COUNT
from tests.fixture_paths import PUZZLES


@test
def page_runs_micropython_and_draws_the_board():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        count = page.locator('g.tile').count()
    assert count == TILE_COUNT


@test
def page_works_from_a_subdirectory():
    with site_server(puzzles_dir=PUZZLES, prefix='sub/') as base:
        with open_page(base) as page:
            count = page.locator('g.tile').count()
    assert base.endswith('/sub/')
    assert count == TILE_COUNT
