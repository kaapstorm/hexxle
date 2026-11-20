"""Helpers for building page elements.

Text goes in through ``textContent`` only, never as markup, so text
from the index, a puzzle or storage cannot become HTML.
"""

from pyscript import document


def element(tag, text=None, class_name=None):
    """A new ``tag`` element with ``text`` and ``class_name``, if given."""
    new = document.createElement(tag)
    if text is not None:
        new.textContent = text
    if class_name is not None:
        new.className = class_name
    return new
