from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import (
    ConsoleMessage,
    Error,
    Page,
    sync_playwright,
)

VIEWPORT = {'width': 390, 'height': 844}
READY_TIMEOUT_MS = 30_000


@contextmanager
def open_page(url: str) -> Iterator[Page]:
    """Open ``url`` in Chromium as a phone and wait for the page to render.

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
            page.goto(url)
            try:
                page.wait_for_selector(
                    'html[data-ready]',
                    state='attached',
                    timeout=READY_TIMEOUT_MS,
                )
            except Exception:
                raise AssertionError(
                    f'page never became ready; console errors: {errors}'
                ) from None
            yield page
        finally:
            browser.close()
    assert errors == [], errors
