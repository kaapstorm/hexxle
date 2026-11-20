import json
import tempfile
from pathlib import Path

from playwright.sync_api import Page
from testsweet import params, test

from hexxle.site import site_server
from tests.browser.support import (
    FAILED_RESOURCE,
    SERVER_ERROR,
    open_page,
    trace,
    wait_until_ready,
)
from tests.core.examples import PATHS
from tests.fixture_paths import BROKEN_PUZZLES, PUZZLES

# Ask for a file that is not there whenever the page fetches the newest
# puzzle, so the server answers 404 although the index lists it.
LOSE_NEWEST_FILE = """
const realFetch = globalThis.fetch;
globalThis.fetch = (url, options) => realFetch(
  String(url).replace('2026-11-20.txt', 'gone.txt'), options);
"""

COULD_NOT_LOAD = (
    'Could not load the puzzle. Check your connection and try again.')
INDEX_URL = '**/puzzles/index.json'
NEWEST_URL = '**/puzzles/2026-11-20.txt'

# Hide the storage wrapper from the page, so reading saved progress
# raises a Python error during start-up.
HIDE_STORAGE = """
Object.defineProperty(globalThis, 'hexxleStorage', {
  get() { return undefined; },
  set(value) {},
});
"""


def show_puzzles(page: Page) -> list[str]:
    """Open the puzzles list and return its links' hrefs."""
    page.locator('#show-puzzles').click()
    links = page.locator('nav#puzzles a')
    links.first.wait_for()
    return [
        links.nth(index).get_attribute('href')
        for index in range(links.count())
    ]


@test
def opens_the_newest_puzzle_by_default():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        title = page.locator('#title').text_content()
    assert '20 Nov 2026' in title


@test
def opens_a_named_puzzle():
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(base + '?p=2026-11-18_express') as page:
            title = page.locator('#title').text_content()
    assert '18 Nov 2026' in title
    assert 'express' in title


@test
def lists_puzzles_newest_first_with_progress():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        trace(page, PATHS['EXACT'])
        hrefs = show_puzzles(page)
        links = page.locator('nav#puzzles a')
        first_text = links.nth(0).text_content()
        first_current = links.nth(0).get_attribute('aria-current')
        second_text = links.nth(1).text_content()
        second_current = links.nth(1).get_attribute('aria-current')
        visible = page.locator('nav#puzzles').is_visible()
    assert hrefs == ['?p=2026-11-20', '?p=2026-11-18_express']
    assert '20 Nov 2026' in first_text
    assert '1 of 2' in first_text
    assert first_current == 'page'
    assert '18 Nov 2026' in second_text
    assert 'express' in second_text
    assert ' of ' not in second_text
    assert second_current is None
    assert visible


@test
def the_button_toggles_the_puzzles_list():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        nav = page.locator('nav#puzzles')
        before = nav.is_visible()
        page.locator('#show-puzzles').click()
        opened = nav.is_visible()
        page.locator('#show-puzzles').click()
        closed = nav.is_visible()
    assert not before
    assert opened
    assert not closed


@test
def following_a_link_opens_that_puzzle():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        show_puzzles(page)
        page.locator('nav#puzzles a').nth(1).click()
        page.wait_for_url('**?p=2026-11-18_express')
        wait_until_ready(page)
        title = page.locator('#title').text_content()
    assert '18 Nov 2026' in title


@test
def refreshes_stale_saved_counts_on_load():
    saved = {'words': ['EXACT', 'GONE'], 'found': 2, 'total': 9}
    script = 'localStorage.setItem(%s, %s);' % (
        json.dumps('hexxle:2026-11-20'), json.dumps(json.dumps(saved)))
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(base, init_script=script) as page:
            show_puzzles(page)
            first_text = page.locator('nav#puzzles a').nth(0).text_content()
    assert '1 of 2' in first_text


@test
@params([
    ('?p=2020-01-01',), ('?p=../index',), ('?p=',), ('?p=2026-11-20.txt',),
])
def reports_an_unknown_puzzle(query):
    # open_page fails the test if the page logs any console error.
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(base + query) as page:
            notice = page.locator('#notice').text_content()
            tiles = page.locator('g.tile').count()
    assert notice == 'Puzzle not found'
    assert tiles == 0


@test
def reports_a_missing_puzzle_file():
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(
            base, init_script=LOSE_NEWEST_FILE, allow_missing=True,
        ) as page:
            notice = page.locator('#notice').text_content()
            tiles = page.locator('g.tile').count()
    assert notice == 'Puzzle not found'
    assert tiles == 0


@test
def reports_no_puzzles():
    notices = []
    with site_server() as base:
        with open_page(base, allow_missing=True) as page:
            notices.append(page.locator('#notice').text_content())
            notices.append(page.locator('g.tile').count())
    with tempfile.TemporaryDirectory() as tmp:
        with site_server(puzzles_dir=Path(tmp)) as base:
            with open_page(base) as page:
                notices.append(page.locator('#notice').text_content())
                notices.append(page.locator('g.tile').count())
    assert notices == ['No puzzles yet', 0, 'No puzzles yet', 0]


@test
def reports_a_broken_puzzle():
    with site_server(puzzles_dir=BROKEN_PUZZLES) as base:
        with open_page(base) as page:
            notice = page.locator('#notice').text_content()
            tiles = page.locator('g.tile').count()
    assert notice.startswith('This puzzle is broken')
    assert 'line 2' in notice
    assert tiles == 0


@test
@params([(INDEX_URL,), (NEWEST_URL,)])
def reports_a_request_that_gets_no_response(url):
    def go_offline(page: Page) -> None:
        page.route(url, lambda route: route.abort())

    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(
            base, prepare=go_offline, allow_errors=(FAILED_RESOURCE,),
        ) as page:
            notice = page.locator('#notice').text_content()
            tiles = page.locator('g.tile').count()
    assert notice == COULD_NOT_LOAD
    assert tiles == 0


@test
@params([
    (500, 'oops', COULD_NOT_LOAD),
    (200, 'not json', COULD_NOT_LOAD),
    (200, '{"2026-11-20": true}', COULD_NOT_LOAD),
    (200, '[1, 2, 3]', 'No puzzles yet'),
])
def reports_an_unusable_index(status, body, expected):
    def serve_index(page: Page) -> None:
        page.route(INDEX_URL, lambda route: route.fulfill(
            status=status, body=body, content_type='application/json'))

    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(
            base, prepare=serve_index, allow_errors=(SERVER_ERROR,),
        ) as page:
            notice = page.locator('#notice').text_content()
            tiles = page.locator('g.tile').count()
    assert notice == expected
    assert tiles == 0


@test
def reports_an_unexpected_error_during_start_up():
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(
            base, init_script=HIDE_STORAGE, allow_errors=('Traceback',),
        ) as page:
            notice = page.locator('#notice').text_content()
            tiles_hidden = page.locator('svg#board').is_hidden()
    assert notice == 'Something went wrong.'
    assert tiles_hidden
