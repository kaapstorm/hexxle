"""The puzzles list: a link to each puzzle with the player's progress.

``button#show-puzzles`` toggles ``nav#puzzles``. Every piece of text
comes from the index or from storage, so it goes into the page with
``textContent`` only.
"""

from pyscript import document
from pyscript.ffi import create_proxy

import store
from dom import element
from hexxle.core.puzzle import describe_identifier


class PuzzleList:
    def __init__(self, index, current):
        """List the identifiers in ``index``, in the order given.

        ``current`` is the identifier being played, or ``None``.
        """
        self._index = index
        self._current = current
        self._button = document.querySelector('#show-puzzles')
        self._nav = document.querySelector('#puzzles')
        self._toggle_proxy = create_proxy(self._toggle)
        self._button.addEventListener('click', self._toggle_proxy)
        self._button.hidden = False

    def _toggle(self, event):
        opening = self._nav.hidden
        if opening:
            # Read progress afresh: it changes as the player finds words.
            self._render()
        self._nav.hidden = not opening
        self._button.setAttribute('aria-expanded', 'true' if opening
                                  else 'false')

    def _render(self):
        items = element('ul')
        for ident in self._index:
            item = element('li')
            item.appendChild(self._link(ident))
            items.appendChild(item)
        self._nav.replaceChildren(items)

    def _link(self, ident):
        link = element('a')
        link.setAttribute('href', '?p=' + ident)
        if ident == self._current:
            link.setAttribute('aria-current', 'page')
        date, label = describe_identifier(ident)
        link.appendChild(element('span', date, 'date'))
        if label:
            link.appendChild(element('span', label, 'label'))
        summary = store.summary(ident)
        if summary is not None:
            link.appendChild(
                element('span', '%d of %d' % summary, 'count'))
        return link
