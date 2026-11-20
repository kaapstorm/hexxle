"""A stand-in for Testsweet, enough to run hexxle's core tests on
MicroPython in the browser.

Only ``test``, ``params`` and ``catch_exceptions`` are provided.
"""

registered = []


def test(fn):
    """Register ``fn`` to be run, and return it."""
    registered.append(fn)
    return fn


def params(rows):
    """Run the decorated function once per row of positional arguments."""
    rows = list(rows)

    def decorate(fn):
        return Parametrized(fn, rows)

    return decorate


class Parametrized:
    """A function with rows of arguments; one test call per row.

    A class rather than attributes on a function, because MicroPython
    functions do not accept attributes.
    """

    def __init__(self, fn, rows):
        self.fn = fn
        self.rows = rows
        self.__name__ = fn.__name__

    def cases(self):
        """Return ``(name, call)`` for each row, named like Testsweet's."""
        return [
            ('%s[%d]' % (self.__name__, index), self._bind(row))
            for index, row in enumerate(self.rows)
        ]

    def _bind(self, row):
        return lambda: self.fn(*row)


class catch_exceptions:  # lower case, as in Testsweet
    """Collect any ``Exception`` raised in the block, without raising it."""

    def __enter__(self):
        self.caught = []
        return self.caught

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None and issubclass(exc_type, Exception):
            self.caught.append(exc)
            return True
        return False
