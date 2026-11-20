import contextlib
import io
import socket
import tempfile
from pathlib import Path

from testsweet import test

import hexxle.site
from hexxle.cli import main
from tests.fixture_paths import EXAMPLE_PATH


def run(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main([str(arg) for arg in argv])
    return code, out.getvalue(), err.getvalue()


@test
def serve_reports_a_port_that_cannot_be_used():
    with socket.socket() as taken:
        taken.bind(('127.0.0.1', 0))
        taken.listen()
        port = taken.getsockname()[1]
        code, out, err = run(['serve', '--puzzles', EXAMPLE_PATH.parent,
                              '--port', port])
    assert code == 1
    assert err.startswith('error: ')
    assert str(port) in err


@test
def serve_reports_a_missing_puzzles_directory():
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / 'puzzles'
        code, out, err = run(['serve', '--puzzles', missing, '--port', 0])
    assert code == 1
    assert err.startswith('error: ')
    assert str(missing) in err


@test
def serve_says_to_run_npm_ci_when_node_modules_is_missing():
    real = hexxle.site.PYSCRIPT_DIST
    with tempfile.TemporaryDirectory() as tmp:
        hexxle.site.PYSCRIPT_DIST = Path(tmp) / 'missing'
        try:
            code, out, err = run(['serve', '--puzzles', EXAMPLE_PATH.parent,
                                  '--port', 0])
        finally:
            hexxle.site.PYSCRIPT_DIST = real
    assert code == 1
    assert err.startswith('error: ')
    assert 'npm ci' in err
