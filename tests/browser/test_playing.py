import json
import tempfile
from pathlib import Path

from playwright.sync_api import Page
from testsweet import params, test

from hexxle.site import site_server
from tests.browser.support import open_page, tile, trace, wait_until_ready
from tests.core.examples import EXAMPLE, PATHS
from tests.fixture_paths import PUZZLES

STORAGE_KEY = 'hexxle:2026-11-20'
# How long a message shows before it fades: MESSAGE_MS in game_view.py.
MESSAGE_MS = 1800

# Stand-ins for the clipboard, which records what is copied, refuses, or
# is missing as it is on a page that is not https or localhost.
RECORD_CLIPBOARD = """
Object.defineProperty(navigator, 'clipboard', {value: {
    writeText: function (text) {
        window.copied = text;
        return Promise.resolve();
    },
}});
"""
REFUSE_CLIPBOARD = """
Object.defineProperty(navigator, 'clipboard', {value: {
    writeText: function () { return Promise.reject(new Error('no')); },
}});
"""
NO_CLIPBOARD = """
Object.defineProperty(navigator, 'clipboard', {value: undefined});
"""

BREAK_STORAGE = """
Storage.prototype.getItem = function () { throw new Error('no storage'); };
Storage.prototype.setItem = function () { throw new Error('no storage'); };
"""


def play(page: Page, word: str) -> tuple[str | None, str]:
    """Trace ``word`` and return ``#message``'s outcome and text."""
    trace(page, PATHS[word])
    return shown_message(page)


def shown_message(page: Page) -> tuple[str | None, str]:
    """``#message``'s outcome and text."""
    message = page.locator('#message')
    return message.get_attribute('data-outcome'), message.text_content()


def is_fading(page: Page) -> bool:
    classes = page.locator('#message').get_attribute('class') or ''
    return 'fading' in classes.split()


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
def reports_each_outcome():
    words = ['TAX', 'EXACT', 'EXACT', 'LUXE', 'ACED']
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        shown = [play(page, word) for word in words]
    assert shown == [
        ('too_short', 'TAX is too short'),
        ('found', 'Found EXACT!'),
        ('already', 'Already found EXACT'),
        ('bonus', 'LUXE is a bonus word!'),
        ('not_a_word', 'ACED is not in this puzzle'),
    ]


@test
def a_word_with_an_emoji_shows_it_when_found():
    themed = (EXAMPLE.replace('EXACT', 'EXACT \U0001f3af')
              .replace('TAXI', 'TAXI \U0001f695')
              .replace('LUXE', 'LUXE \u2728'))
    words = ['LUXE', 'EXACT', 'EXACT', 'TAXI']
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / '2026-11-20.txt').write_text(themed, encoding='utf-8')
        with site_server(puzzles_dir=Path(tmp)) as base:
            with open_page(base) as page:
                shown = [play(page, word)[1] for word in words]
    assert shown == [
        'LUXE is a bonus word! \u2728',
        'Found EXACT! \U0001f3af',
        'Already found EXACT',
        'Found TAXI. \U0001f695 Puzzle complete!',
    ]


@test
def the_message_fades_and_is_cleared():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        page.clock.install()
        play(page, 'EXACT')
        page.clock.run_for(MESSAGE_MS - 100)
        shown = shown_message(page), is_fading(page)
        page.clock.run_for(200)
        fading = shown_message(page), is_fading(page)
        page.clock.run_for(400)
        cleared = shown_message(page), is_fading(page)
    assert shown == (('found', 'Found EXACT!'), False)
    assert fading == (('found', 'Found EXACT!'), True)
    assert cleared == ((None, ''), False)


@test
def a_new_message_gets_its_full_time():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        page.clock.install()
        play(page, 'EXACT')
        page.clock.run_for(1500)
        play(page, 'LUXE')
        page.clock.run_for(MESSAGE_MS - 100)
        shown = shown_message(page), is_fading(page)
        page.clock.run_for(200)
        fading = is_fading(page)
        page.clock.run_for(400)
        cleared = shown_message(page)
    assert shown == (('bonus', 'LUXE is a bonus word!'), False)
    assert fading
    assert cleared == (None, '')


@test
def a_message_shown_during_a_fade_is_not_faded():
    with site_server(puzzles_dir=PUZZLES) as base, open_page(base) as page:
        page.clock.install()
        play(page, 'EXACT')
        page.clock.run_for(MESSAGE_MS + 100)
        was_fading = is_fading(page)
        play(page, 'LUXE')
        page.clock.run_for(1000)
        shown = shown_message(page), is_fading(page)
    assert was_fading
    assert shown == (('bonus', 'LUXE is a bonus word!'), False)


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


def share(page: Page) -> tuple[str | None, str]:
    """Press Share and return the message it leads to."""
    page.locator('#share').click()
    page.wait_for_function(
        "document.querySelector('#message').textContent !== ''")
    return shown_message(page)


@test
def sharing_copies_progress_and_a_link_to_the_puzzle():
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(base, init_script=RECORD_CLIPBOARD) as page:
            play(page, 'EXACT')
            page.clock.install()
            page.clock.run_for(5000)
            message = share(page)
            copied = page.evaluate('window.copied')
    assert message == ('copied', 'Copied to clipboard')
    assert copied == (
        'Hexxle · 20 Nov 2026\n'
        'Found 1 of 2 words.\n'
        f'{base}?p=2026-11-20')


@test
@params([(REFUSE_CLIPBOARD,), (NO_CLIPBOARD,)])
def sharing_says_when_it_could_not_copy(script):
    with site_server(puzzles_dir=PUZZLES) as base:
        with open_page(base, init_script=script) as page:
            message = share(page)
    assert message == ('not_copied', 'Could not copy')
