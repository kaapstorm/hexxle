"""Run hexxle's core tests under MicroPython and show the results.

Imports each module named in ``tests/core/manifest.json`` and runs what
the stand-in ``testsweet`` registered. Writes one line per module
(``MODULE name``) and per test call (``PASS name`` or
``FAIL name: message``) to ``#results``, then sets the ready flag. A
module that registers no tests is a ``FAIL``: its decorators did not
work here.
"""

import json
import sys

from pyscript import document

import testsweet

PACKAGE = 'tests.core'
MANIFEST = 'tests/core/manifest.json'


def describe(error):
    message = str(error)
    if message:
        return '%s: %s' % (type(error).__name__, message)
    return type(error).__name__


def run_call(name, call, lines):
    try:
        call()
    except Exception as error:
        sys.print_exception(error)
        lines.append('FAIL %s: %s' % (name, describe(error)))
        return False
    lines.append('PASS %s' % name)
    return True


def run_module(name, lines):
    lines.append('MODULE %s' % name)
    del testsweet.registered[:]
    dotted = PACKAGE + '.' + name
    try:
        __import__(dotted)
    except Exception as error:
        sys.print_exception(error)
        lines.append('FAIL %s: %s' % (name, describe(error)))
        return False
    if not testsweet.registered:
        lines.append('FAIL %s: no tests registered' % name)
        return False
    ok = True
    for fn in list(testsweet.registered):
        if isinstance(fn, testsweet.Parametrized):
            cases = fn.cases()
        else:
            cases = [(fn.__name__, fn)]
        for case_name, call in cases:
            ok = run_call(case_name, call, lines) and ok
    return ok


def main():
    with open(MANIFEST) as f:
        modules = json.load(f)
    lines = []
    ok = True
    for name in modules:
        ok = run_module(name, lines) and ok
    results = document.querySelector('#results')
    results.innerText = '\n'.join(lines)
    results.dataset.status = 'pass' if ok else 'fail'
    document.documentElement.dataset.ready = '1'


main()
