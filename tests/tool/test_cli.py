import contextlib
import inspect
import io
import shutil
import socket
import tempfile
from pathlib import Path

from testsweet import params, test

import hexxle.site
from hexxle.cli import main
from hexxle.config import CONFIG_PATH
from tests.core.examples import EXAMPLE
from tests.fixture_paths import EXAMPLE_PATH, FIXTURES, WORDS_PATH

# A settings file that does not exist, so tests never read the real one.
NO_SETTINGS = FIXTURES / 'no-such-hexxle.toml'

SOLVED = (' T A U\nS C X L\n S E I\nE D C N\n\n---\n'
          'ACED\nAXED\nLUXE\nTAXI\n\nEXACT\n')
BOARD = ' T A U\nS C X L\n S E I\nE D C N\n'


def run(argv, config_path=NO_SETTINGS):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main([str(arg) for arg in argv], config_path=config_path)
    return code, out.getvalue(), err.getvalue()


@test
def solve_prints_a_puzzle_file():
    code, out, err = run(['solve', EXAMPLE_PATH, '-d', WORDS_PATH])
    assert code == 0
    assert out == SOLVED


@test
def check_exits_zero_for_a_good_puzzle():
    code, out, err = run(['check', EXAMPLE_PATH, '-d', WORDS_PATH])
    lines = err.splitlines()
    assert code == 0
    assert len(lines) == 2
    assert all(line.startswith('warning: ') for line in lines)


@test
def check_exits_one_and_names_the_problem():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / '2026-11-20.txt'
        path.write_text(EXAMPLE.replace('TAXI', 'TAXIS'))
        code, out, err = run(['check', path, '-d', WORDS_PATH])
    assert code == 1
    assert 'error: ' in err
    assert 'TAXIS' in err


@test
@params([('solve',), ('check',)])
def a_missing_file_is_an_error_not_a_traceback(command):
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / 'nothing.txt'
        code, out, err = run([command, missing, '-d', WORDS_PATH])
        code2, out2, err2 = run([command, EXAMPLE_PATH, '-d', missing])
    assert code == 1
    assert err.startswith('error: ')
    assert 'Traceback' not in err
    assert code2 == 1
    assert err2.startswith('error: ')
    assert 'Traceback' not in err2


@test
@params([
    (BOARD,),
    (BOARD + '\n--- extras\nAB-CD\n',),
])
def solve_ignores_word_sections(text):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / '2026-11-20.txt'
        path.write_text(text)
        code, out, err = run(['solve', path, '-d', WORDS_PATH])
    assert code == 0
    assert out == SOLVED
    assert err == ''


@test
def the_dictionary_setting_is_relative_to_the_settings_file():
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / 'hexxle.toml'
        settings.write_text('dictionary = "lists/words"\n')
        (Path(tmp) / 'lists').mkdir()
        shutil.copy(WORDS_PATH, Path(tmp) / 'lists' / 'words')
        code, out, err = run(['solve', EXAMPLE_PATH], config_path=settings)
    assert code == 0
    assert out == SOLVED


@test
def settings_are_read_from_the_repository_root_by_default():
    default = inspect.signature(main).parameters['config_path'].default
    assert default == CONFIG_PATH


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
