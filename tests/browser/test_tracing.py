from playwright.sync_api import Page
from testsweet import test

from hexxle.site import site_server
from tests.browser.support import centre, open_page, tile, trace
from tests.core.examples import PATHS, TILE_COUNT
from tests.fixture_paths import PUZZLES

T, A, X, L = (1, 0), (3, 0), (4, 1), (6, 1)
EXACT = PATHS['EXACT']
# How far into the page gutter "beside the board" moves go; small enough
# to stay inside the viewport.
BESIDE_PX = 3

RECORD_POINTER_ID = """
window.addEventListener('pointerdown', (event) => {
  window.lastPointerId = event.pointerId;
}, {capture: true});
"""


def board_box(page: Page) -> dict:
    return page.locator('svg#board').bounding_box()


def dispatch(page: Page, selector: str, kind: str, pointer_id: int) -> None:
    page.evaluate(
        """([selector, kind, pointerId]) => {
          const target = document.querySelector(selector);
          const box = target.getBoundingClientRect();
          target.dispatchEvent(new PointerEvent(kind, {
            pointerId,
            bubbles: true,
            cancelable: true,
            clientX: box.x + box.width / 2,
            clientY: box.y + box.height / 2,
          }));
        }""",
        [selector, kind, pointer_id],
    )


@test
def draws_one_tile_per_letter():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        count = page.locator('g.tile').count()
        letter = tile(page, X).locator('text.letter').text_content()
    assert count == TILE_COUNT
    assert letter == 'X'


@test
def tracing_shows_the_word_and_marks_tiles():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        trace(page, EXACT, release=False)
        word = page.locator('#word').text_content()
        marked = page.locator('g.tile.in-path').count()
        points = page.locator('#trace-line').get_attribute('points')
    assert word == 'EXACT'
    assert marked == 5
    assert len(points.split()) == 5


@test
def releasing_submits_the_word():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        trace(page, EXACT)
        message = page.locator('#message').text_content()
        word = page.locator('#word').text_content()
        marked = page.locator('g.tile.in-path').count()
    assert message == 'Found!'
    assert word == ''
    assert marked == 0


@test
def dragging_back_removes_a_letter():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        trace(page, [T, A, X, A], release=False)
        word = page.locator('#word').text_content()
    assert word == 'TA'


@test
def dragging_above_the_board_arms_a_cancel():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        trace(page, [T, A], release=False)
        x, _ = centre(tile(page, A))
        page.mouse.move(x, board_box(page)['y'] - 20, steps=5)
        classes = page.locator('#word').get_attribute('class') or ''
        page.mouse.up()
        message = page.locator('#message').text_content()
        word = page.locator('#word').text_content()
    assert 'cancelling' in classes.split()
    assert message == ''
    assert word == ''


@test
def dragging_back_onto_the_board_disarms():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        trace(page, [T, A], release=False)
        x, _ = centre(tile(page, A))
        page.mouse.move(x, board_box(page)['y'] - 20, steps=5)
        page.mouse.move(*centre(tile(page, A)), steps=5)
        page.mouse.move(*centre(tile(page, X)), steps=5)
        classes = page.locator('#word').get_attribute('class') or ''
        page.mouse.up()
        message = page.locator('#message').text_content()
    assert 'cancelling' not in classes.split()
    assert message == 'Too short'


@test
def releasing_beside_the_board_still_submits():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        trace(page, [X, L], release=False)
        box = board_box(page)
        _, y = centre(tile(page, L))
        page.mouse.move(box['x'] + box['width'] + BESIDE_PX, y, steps=5)
        page.mouse.up()
        message = page.locator('#message').text_content()
    assert message == 'Too short'


@test
def a_right_button_press_starts_no_trace():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        page.mouse.move(*centre(tile(page, T)))
        page.mouse.down(button='right')
        word = page.locator('#word').text_content()
        marked = page.locator('g.tile.in-path').count()
        page.mouse.up(button='right')
    assert word == ''
    assert marked == 0


@test
def a_second_pointer_is_ignored():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        trace(page, [T, A], release=False)
        selector = 'g.tile[data-pos="6,3"] polygon'
        dispatch(page, selector, 'pointerdown', 99)
        dispatch(page, selector, 'pointerup', 99)
        page.mouse.move(*centre(tile(page, X)), steps=5)
        page.mouse.up()
        message = page.locator('#message').text_content()
    assert message == 'Too short'


@test
def a_system_cancel_discards_the_trace():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        page.evaluate(RECORD_POINTER_ID)
        trace(page, [T, A], release=False)
        pointer_id = page.evaluate('window.lastPointerId')
        dispatch(page, 'svg#board', 'pointercancel', pointer_id)
        message = page.locator('#message').text_content()
        word = page.locator('#word').text_content()
    assert message == ''
    assert word == ''
