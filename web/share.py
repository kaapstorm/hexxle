"""The Share button: copy the player's progress to the clipboard.

``button#share`` copies ``hexxle.core.share.share_text``. The clipboard
exists only on https or localhost, and a copy can be refused; either
way the player is told, and nothing else changes. ``writeText`` reports
a refusal by rejecting its promise, never by throwing.
"""

from pyscript import document, window
from pyscript.ffi import create_proxy

from hexxle.core.share import share_text

COPIED = 'copied'
NOT_COPIED = 'not_copied'
MESSAGES = {
    COPIED: 'Copied to clipboard',
    NOT_COPIED: 'Could not copy',
}


def puzzle_url(ident):
    """The address of the puzzle ``ident`` on this site."""
    location = window.location
    return '%s%s?p=%s' % (location.origin, location.pathname, ident)


class ShareButton:
    def __init__(self, ident, game, show_message):
        """``show_message(text, kind)`` tells the player what happened."""
        self._ident = ident
        self._game = game
        self._show_message = show_message
        self._click_proxy = create_proxy(self._share)
        self._copied_proxy = create_proxy(self._copied)
        self._refused_proxy = create_proxy(self._refused)
        button = document.querySelector('#share')
        button.addEventListener('click', self._click_proxy)
        button.hidden = False

    def _share(self, event):
        text = share_text(self._ident, self._game, puzzle_url(self._ident))
        try:
            copying = window.navigator.clipboard.writeText(text)
        except AttributeError:
            # No clipboard: MicroPython has no ``writeText`` to call on
            # JavaScript's ``undefined``.
            self._refused()
            return
        copying.then(self._copied_proxy, self._refused_proxy)

    def _copied(self, *_args):
        self._show_message(MESSAGES[COPIED], COPIED)

    def _refused(self, *_args):
        self._show_message(MESSAGES[NOT_COPIED], NOT_COPIED)
