import json

from playwright.sync_api import Page
from testsweet import params, test

from hexxle.site import site_server
from tests.browser.support import open_page, tile, trace, wait_until_ready
from tests.core.examples import PATHS
from tests.fixture_paths import PUZZLES

STORAGE_KEY = 'hexxle:2026-11-20'

BREAK_STORAGE = """
Storage.prototype.getItem = function () { throw new Error('no storage'); };
Storage.prototype.setItem = function () { throw new Error('no storage'); };
"""


def play(page: Page, word: str) -> tuple[str, str]:
    """Trace ``word`` and return ``#message``'s outcome and text."""
    trace(page, PATHS[word])
    message = page.locator('#message')
    return message.get_attribute('data-outcome'), message.text_content()


def hints(page: Page, pos: tuple[int, int]) -> tuple[str, str]:
    group = tile(page, pos)
    return (
        group.locator('text.hint-starts').text_content(),
        group.locator('text.hint-uses').text_content(),
    )


def is_dimmed(page: Page, pos: tuple[int, int]) -> bool:
    classes = tile(page, pos).get_attribute('class') or ''
    return 'dimmed' in classes.split()


def listed(page: Page, group: str) -> list[str]:
    selector = f'#found section[data-group="{group}"] li'
    return page.locator(selector).all_text_contents()


@test
def shows_the_date():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        title = page.locator('#title').text_content()
    assert '20 Nov 2026' in title


@test
@params([
    ('TAX', 'too_short', 'TAX is too short'),
    ('EXACT', 'found', 'Found EXACT!'),
    ('LUXE', 'bonus', 'LUXE is a bonus word!'),
    ('ACED', 'not_a_word', 'ACED is not in this puzzle'),
])
def reports_each_outcome(word, outcome, text):
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        shown_outcome, shown_text = play(page, word)
    assert shown_outcome == outcome
    assert shown_text == text


@test
def reports_a_repeat():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        play(page, 'EXACT')
        outcome, text = play(page, 'EXACT')
    assert outcome == 'already'
    assert text == 'Already found EXACT'


@test
def shows_progress_and_found_words():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        before = page.locator('#progress').text_content()
        play(page, 'EXACT')
        play(page, 'LUXE')
        after = page.locator('#progress').text_content()
        five_letters = listed(page, '5')
        bonus = listed(page, 'bonus')
    assert before == '0 of 2 words'
    assert after == '1 of 2 words · 1 bonus'
    assert five_letters == ['EXACT']
    assert bonus == ['LUXE']


@test
def shows_hints_and_dims_tiles():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        t_before = hints(page, (1, 0))
        l_hints = hints(page, (6, 1))
        l_dimmed = is_dimmed(page, (6, 1))
        i_dimmed_before = is_dimmed(page, (5, 2))
        play(page, 'TAXI')
        i_dimmed_after = is_dimmed(page, (5, 2))
        t_after = hints(page, (1, 0))
    assert t_before == ('1', '2')
    assert l_hints == ('', '')
    assert l_dimmed
    assert not i_dimmed_before
    assert i_dimmed_after
    assert t_after == ('', '1')


@test
def completes_the_puzzle():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        play(page, 'EXACT')
        _, text = play(page, 'TAXI')
        body_classes = page.locator('body').get_attribute('class') or ''
        _, bonus_text = play(page, 'LUXE')
    assert text == 'Found TAXI. Puzzle complete!'
    assert 'complete' in body_classes.split()
    assert bonus_text == 'LUXE is a bonus word!'


@test
def remembers_progress_across_reloads():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        play(page, 'EXACT')
        page.reload()
        wait_until_ready(page)
        progress = page.locator('#progress').text_content()
        outcome, text = play(page, 'EXACT')
    assert progress == '1 of 2 words'
    assert outcome == 'already'
    assert text == 'Already found EXACT'


@test
@params([('not json',), ('{"words": 7}',), ('[]',)])
def plays_despite_corrupt_saved_progress(value):
    script = 'localStorage.setItem(%s, %s);' % (
        json.dumps(STORAGE_KEY), json.dumps(value))
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(base, init_script=script) as page:
            progress = page.locator('#progress').text_content()
            _, text = play(page, 'EXACT')
    assert progress == '0 of 2 words'
    assert text == 'Found EXACT!'


@test
def plays_when_storage_is_unavailable():
    # open_page fails the test if the page logs any console error.
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(base, init_script=BREAK_STORAGE) as page:
            _, text = play(page, 'EXACT')
            progress = page.locator('#progress').text_content()
    assert progress == '1 of 2 words'
    assert text == 'Found EXACT!'
