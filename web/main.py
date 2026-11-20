from pyscript import document, fetch

import store
from board_view import BoardView
from game_view import GameView
from hexxle.core.game import BONUS, FOUND, Game
from hexxle.core.puzzle import parse_puzzle


def on_submit(word):
    outcome = game.submit(word)
    game_view.show_outcome(outcome)
    if outcome in (FOUND, BONUS):
        store.save(ident, game)
        game_view.refresh()
    if outcome == FOUND:
        board_view.show_hints(game)


index = await fetch('./puzzles/index.json').json()  # noqa: F704
ident = index[0]
text = await fetch('./puzzles/%s.txt' % ident).text()  # noqa: F704
puzzle = parse_puzzle(text)
game = Game(puzzle, store.load(ident))
board_view = BoardView(puzzle.board, on_submit)
board_view.show_hints(game)
game_view = GameView(game, ident)
document.documentElement.dataset.ready = '1'
