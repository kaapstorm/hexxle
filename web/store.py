"""Keep each puzzle's progress in the browser's ``localStorage``.

Storage is a convenience: it may be missing, full, blocked or hold
anything at all. Every function here swallows those failures, so the
game always stays playable, at worst without saved progress.

``localStorage`` is reached only through ``hexxleStorage`` in
``storage.js``: MicroPython's FFI cannot catch an exception thrown by a
JS function, so the calls that may throw are made from JS.
"""

import json

from pyscript import window
from pyscript.ffi import is_none


def _key(ident):
    return 'hexxle:' + ident


def _read(ident):
    """The saved object for ``ident``, or ``None`` if absent or bad."""
    text = window.hexxleStorage.get(_key(ident))
    if is_none(text):
        return None
    try:
        data = json.loads(text)
    except Exception:
        return None
    if isinstance(data, dict):
        return data
    return None


def load(ident):
    """The words saved for ``ident``, or ``[]``."""
    data = _read(ident)
    if data is None:
        return []
    words = data.get('words')
    if not isinstance(words, list):
        return []
    for word in words:
        if not isinstance(word, str):
            return []
    return words


def save(ident, game):
    found, total, _ = game.progress()
    text = json.dumps(
        {'words': game.found_words(), 'found': found, 'total': total})
    window.hexxleStorage.set(_key(ident), text)


def summary(ident):
    """``(found, total)`` saved for ``ident``, or ``None``."""
    data = _read(ident)
    if data is None:
        return None
    found = data.get('found')
    total = data.get('total')
    if not isinstance(found, int) or not isinstance(total, int):
        return None
    return found, total
