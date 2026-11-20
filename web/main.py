from pyscript import document, fetch

from board_view import BoardView
from hexxle.core.puzzle import parse_puzzle


def show_submitted(word):
    document.querySelector('#message').textContent = word


index = await fetch('./puzzles/index.json').json()  # noqa: F704
text = await fetch('./puzzles/%s.txt' % index[0]).text()  # noqa: F704
view = BoardView(parse_puzzle(text).board, show_submitted)
document.documentElement.dataset.ready = '1'
