"""Choose a puzzle, load it and start the game.

``?p=<identifier>`` picks the puzzle; without it, the first in the
index (the newest). Problems are shown in ``#notice`` instead of a board.

A 404 resolves normally, so it is found from ``response.status``. A
fetch that gets no response at all (offline) rejects; an awaited
rejection arrives as a catchable Python exception. Only a JS function
that throws synchronously cannot be caught from MicroPython (see
``storage.js``).
"""

import io
import sys

from pyscript import document, fetch, window

import store
from board_view import BoardView
from game_view import GameView
from hexxle.core.board import PuzzleError
from hexxle.core.game import BONUS, FOUND, Game
from hexxle.core.index import (
    INDEX_NAME,
    PUZZLES_DIR,
    choose,
    file_name_of,
    parse_index,
)
from hexxle.core.puzzle import parse_puzzle
from puzzle_list import PuzzleList
from share import ShareButton

PUZZLES = './' + PUZZLES_DIR + '/'
NO_PUZZLES = 'No puzzles yet'
NOT_FOUND = 'Puzzle not found'
BROKEN = 'This puzzle is broken'
COULD_NOT_LOAD = (
    'Could not load the puzzle. Check your connection and try again.')
SOMETHING_WRONG = 'Something went wrong.'
HTTP_NOT_FOUND = 404


class LoadError(Exception):
    """The server could not be reached or did not send the file."""


puzzle_list = None


def on_submit(word):
    outcome = game.submit(word)
    game_view.show_outcome(outcome, word)
    if outcome in (FOUND, BONUS):
        store.save(ident, game)
        game_view.refresh()
    if outcome == FOUND:
        board_view.show_hints(game)


async def fetch_text(url):
    """The text at ``url``, or ``None`` if the server answered 404.

    Raises ``LoadError`` if there is no response or another error status.
    """
    try:
        # 'no-cache' revalidates, so a newly published or replaced
        # puzzle shows up without a hard reload.
        response = await fetch(url, cache='no-cache')
        if response.ok:
            return await response.text()
    except Exception as error:
        # A rejected fetch: no response at all, or the body was cut off.
        raise LoadError('%s: %s' % (url, error))
    if response.status == HTTP_NOT_FOUND:
        return None
    raise LoadError('%s: status %d' % (url, response.status))


def requested_puzzle():
    """The ``p`` query parameter, or ``None`` if there is none."""
    params = window.URLSearchParams.new(window.location.search)
    if not params.has('p'):
        return None
    return params.get('p')


def show_notice(text):
    document.querySelector('#notice').textContent = text
    document.body.classList.add('notice')


def log_error(error):
    """Write ``error`` and its traceback to the browser console."""
    trace = io.StringIO()
    sys.print_exception(error, trace)
    window.console.error(trace.getvalue())


async def load_index():
    """The identifiers in the index, newest first.

    A missing or empty index gives ``[]``. Raises ``LoadError`` if the
    index cannot be fetched or is not a JSON list.
    """
    text = await fetch_text(PUZZLES + INDEX_NAME)
    if text is None:
        return []
    try:
        return parse_index(text)
    except ValueError as error:
        raise LoadError('%s: %s' % (INDEX_NAME, error))


async def start():
    """Load the chosen puzzle and set up the puzzles list.

    Returns ``(ident, puzzle, game)``, or ``None`` after showing a
    notice.
    """
    index = await load_index()
    if not index:
        show_notice(NO_PUZZLES)
        return None
    chosen = choose(index, requested_puzzle())
    # Kept at module level so its click handler lives as long as the page.
    global puzzle_list
    puzzle_list = PuzzleList(index, chosen)
    if chosen is None:
        show_notice(NOT_FOUND)
        return None
    text = await fetch_text(PUZZLES + file_name_of(chosen))
    if text is None:
        show_notice(NOT_FOUND)
        return None
    try:
        puzzle = parse_puzzle(text)
    except PuzzleError as error:
        show_notice('%s: %s' % (BROKEN, error))
        return None
    saved = store.load(chosen)
    game = Game(puzzle, saved)
    if saved:
        # Refresh the saved counts, which go stale if the puzzle was
        # republished, so the puzzles list shows the true progress.
        store.save(chosen, game)
    return chosen, puzzle, game


# Whatever happens, the page ends up showing a board or a notice, and
# is marked ready.
try:
    # PyScript runs this file with top-level await enabled; no ``async``
    # attribute is needed on the script tag.
    started = await start()  # noqa: F704
    if started is not None:
        ident, puzzle, game = started
        board_view = BoardView(puzzle.board, on_submit)
        board_view.show_hints(game)
        game_view = GameView(game, ident)
        # Kept so that its click handler lives as long as the page.
        share_button = ShareButton(ident, game, game_view.show_message)
except LoadError as error:
    window.console.warn('Hexxle could not load: %s' % error)
    show_notice(COULD_NOT_LOAD)
except Exception as error:
    log_error(error)
    show_notice(SOMETHING_WRONG)
finally:
    document.documentElement.dataset.ready = '1'
