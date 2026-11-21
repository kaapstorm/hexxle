"""Show the game's state around the board: title, outcome, progress and
the words found so far.

All rules live in ``hexxle.core.game.Game``; this module only renders
what it reports.
"""

from pyscript import document, window
from pyscript.ffi import create_proxy

from dom import element
from hexxle.core.game import ALREADY, BONUS, FOUND, NOT_A_WORD, TOO_SHORT
from hexxle.core.puzzle import describe_identifier

# Each takes the submitted word.
MESSAGES = {
    TOO_SHORT: '%s is too short',
    FOUND: 'Found %s!',
    BONUS: '%s is a bonus word!',
    ALREADY: 'Already found %s',
    NOT_A_WORD: '%s is not in this puzzle',
}
COMPLETE_MESSAGE = 'Found %s. Puzzle complete!'
MESSAGE_MS = 2000


class GameView:
    def __init__(self, game, ident):
        self._game = game
        self._message = document.querySelector('#message')
        self._clear_proxy = create_proxy(self._clear_message)
        self._clear_timers = 0
        self._progress = document.querySelector('#progress')
        self._found = document.querySelector('#found')
        date, label = describe_identifier(ident)
        title = date
        if label:
            title = '%s · %s' % (date, label)
        document.querySelector('#title').textContent = title
        self.refresh()

    def show_outcome(self, outcome, word):
        """Say what became of ``word``, for ``MESSAGE_MS`` milliseconds."""
        text = MESSAGES[outcome]
        if outcome == FOUND and self._game.is_complete():
            text = COMPLETE_MESSAGE
        self._message.dataset.outcome = outcome
        self._message.textContent = text % word
        self._clear_timers += 1
        window.setTimeout(self._clear_proxy, MESSAGE_MS)

    def _clear_message(self, *_args):
        # Only the newest message's timer clears, so that a message which
        # replaced another gets its full time.
        self._clear_timers -= 1
        if self._clear_timers:
            return
        self._message.removeAttribute('data-outcome')
        self._message.textContent = ''

    def refresh(self):
        """Redraw progress, the found words and completion."""
        found, total, bonus = self._game.progress()
        progress = '%d of %d words' % (found, total)
        if bonus:
            progress += ' · %d bonus' % bonus
        self._progress.textContent = progress

        sections = []
        for length, words in self._game.found_groups():
            sections.append(
                self._section(str(length), '%d letters' % length, words))
        bonus_words = self._game.found_bonus()
        if bonus_words:
            sections.append(self._section('bonus', 'Bonus', bonus_words))
        self._found.replaceChildren(*sections)

        document.body.classList.toggle('complete', self._game.is_complete())

    def _section(self, group, heading, words):
        section = element('section')
        section.dataset.group = group
        section.appendChild(element('h2', heading))
        items = element('ul')
        for word in words:
            items.appendChild(element('li', word))
        section.appendChild(items)
        return section
