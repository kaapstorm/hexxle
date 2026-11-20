import importlib

from testsweet import run, test

from hexxle.site import CORE_TESTS, site_server
from tests.browser.support import open_page


def cpython_test_calls() -> list[str]:
    """``module test_call`` for each core test call Testsweet makes."""
    calls = []
    for path in sorted(CORE_TESTS.glob('test_*.py')):
        module = importlib.import_module('tests.core.' + path.stem)
        calls += ['%s %s' % (path.stem, result.name)
                  for result in run(module)]
    return sorted(calls)


def micropython_passes(lines: list[str]) -> list[str]:
    """``module test_call`` for each ``PASS`` line in the results."""
    passes = []
    module = None
    for line in lines:
        if line.startswith('MODULE '):
            module = line.removeprefix('MODULE ')
        elif line.startswith('PASS '):
            passes.append('%s %s' % (module, line.removeprefix('PASS ')))
    return sorted(passes)


@test
def core_tests_pass_under_micropython():
    with site_server(with_tests=True) as base:
        with open_page(base + 'tests.html') as page:
            results = page.locator('#results')
            status = results.get_attribute('data-status')
            lines = results.inner_text().splitlines()
    failures = [line for line in lines if line.startswith('FAIL ')]
    passes = micropython_passes(lines)
    expected = cpython_test_calls()
    assert failures == []
    assert status == 'pass'
    assert len(passes) == len(expected)
    assert passes == expected
