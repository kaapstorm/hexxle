from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import (
    ConsoleMessage,
    Error,
    Locator,
    Page,
    sync_playwright,
)

VIEWPORT = {'width': 390, 'height': 844}
READY_TIMEOUT_MS = 30_000
STEPS_PER_TILE = 5


def tile(page: Page, pos: tuple[int, int]) -> Locator:
    """The ``g.tile`` element at board position ``pos``."""
    column, row = pos
    return page.locator(f'g.tile[data-pos="{column},{row}"]')


def centre(locator: Locator) -> tuple[float, float]:
    """The centre of ``locator``'s bounding box, in page pixels."""
    box = locator.bounding_box()
    return box['x'] + box['width'] / 2, box['y'] + box['height'] / 2


def trace(
    page: Page,
    positions: list[tuple[int, int]],
    release: bool = True,
) -> None:
    """Drag the mouse through the tiles at ``positions``.

    Presses at the first tile's centre and moves to each following
    tile's centre in several steps. Releases at the end if ``release``.
    """
    page.mouse.move(*centre(tile(page, positions[0])))
    page.mouse.down()
    for pos in positions[1:]:
        page.mouse.move(*centre(tile(page, pos)), steps=STEPS_PER_TILE)
    if release:
        page.mouse.up()


def wait_until_ready(page: Page) -> None:
    """Wait until the page's Python has drawn the board and is playable."""
    page.wait_for_selector(
        'html[data-ready]', state='attached', timeout=READY_TIMEOUT_MS)


@contextmanager
def open_page(url: str, init_script: str | None = None) -> Iterator[Page]:
    """Open ``url`` in Chromium as a phone and wait for the page to render.

    ``init_script``, if given, is JavaScript run in the page before any
    of the page's own scripts, on every load.

    Fails if the page logs any console error or raises an uncaught
    exception, whether before or after it becomes ready.
    """
    errors = []

    def on_console(message: ConsoleMessage) -> None:
        if message.type == 'error':
            errors.append(message.text)

    def on_page_error(error: Error) -> None:
        errors.append(str(error))

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            context = browser.new_context(viewport=VIEWPORT, has_touch=True)
            page = context.new_page()
            page.on('console', on_console)
            page.on('pageerror', on_page_error)
            if init_script is not None:
                page.add_init_script(init_script)
            page.goto(url)
            try:
                wait_until_ready(page)
            except Exception:
                raise AssertionError(
                    f'page never became ready; console errors: {errors}'
                ) from None
            yield page
        finally:
            browser.close()
    assert errors == [], errors
