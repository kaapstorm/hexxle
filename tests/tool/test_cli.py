import contextlib
import io
import shutil
import socket
import tempfile
from pathlib import Path

from testsweet import catch_exceptions, params, test

import hexxle.site
from hexxle.cli import main
from tests.core.examples import EXAMPLE
from tests.fixture_paths import EXAMPLE_PATH, FIXTURES, WORDS_PATH
from tests.tool.fake_sftp import FakeSftp, RefusingSftp
# A settings file that does not exist, so tests never read the real one.
NO_SETTINGS = FIXTURES / 'no-such-hexxle.toml'

SOLVED = (' T A U\nS C X L\n S E I\nE D C N\n\n---\n'
          'ACED\nAXED\nLUXE\nTAXI\n\nEXACT\n')
BOARD = ' T A U\nS C X L\n S E I\nE D C N\n'


def no_uploads(host, commands):
    raise AssertionError('unexpected upload to %s' % host)


def run(argv, run_batch=no_uploads, config_path=NO_SETTINGS):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(
            [str(arg) for arg in argv],
            run_batch=run_batch, config_path=config_path)
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
@params([
    (['publish', EXAMPLE_PATH, '-d', WORDS_PATH],),
    (['deploy'],),
])
def a_missing_remote_is_an_error(argv):
    code, out, err = run(argv)
    assert code == 1
    assert err == 'error: no remote configured\n'


@test
def publish_uploads_and_prints_the_identifier_and_warnings():
    fake = FakeSftp()
    code, out, err = run(
        ['publish', EXAMPLE_PATH, '-d', WORDS_PATH,
         '--remote', 'host:/srv/x'],
        run_batch=fake)
    warnings = err.splitlines()
    assert code == 0
    assert out == 'published 2026-11-20\n'
    assert len(warnings) == 2
    assert all(line.startswith('warning: ') for line in warnings)
    assert fake.uploaded['/srv/x/puzzles/2026-11-20.txt'] == EXAMPLE


@test
@params([([], 1), (['--force'], 0)])
def publish_replaces_a_puzzle_only_with_force(flags, expected_code):
    fake = FakeSftp('/srv/x/puzzles/2026-11-20.txt\n')
    code, out, err = run(
        ['publish', EXAMPLE_PATH, '-d', WORDS_PATH,
         '--remote', 'host:/srv/x'] + flags,
        run_batch=fake)
    replaced = '/srv/x/puzzles/2026-11-20.txt' in fake.uploaded
    assert code == expected_code
    assert replaced == (expected_code == 0)


@test
@params([
    ([], 'settings-host'),
    (['--remote', 'flag-host:/srv/b'], 'flag-host'),
])
def the_remote_option_overrides_the_settings_file(flags, expected_host):
    fake = FakeSftp()
    with tempfile.TemporaryDirectory() as tmp:
        settings = Path(tmp) / 'hexxle.toml'
        settings.write_text('remote = "settings-host:/srv/a"\n')
        code, out, err = run(
            ['publish', EXAMPLE_PATH, '-d', WORDS_PATH] + flags,
            run_batch=fake, config_path=settings)
    hosts = {host for host, _ in fake.calls}
    assert code == 0
    assert hosts == {expected_host}


@test
def publish_prints_each_error_in_the_puzzle():
    fake = FakeSftp()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'puzzle.txt'
        path.write_text(EXAMPLE.replace('TAXI', 'TAXIS'))
        code, out, err = run(
            ['publish', path, '-d', WORDS_PATH, '--remote', 'host:/x'],
            run_batch=fake)
    lines = err.splitlines()
    assert code == 1
    assert out == ''
    assert len(lines) == 2
    assert all(line.startswith('error: ') for line in lines)
    assert 'puzzle.txt' in lines[0]
    assert 'TAXIS' in lines[1]
    assert fake.calls == []


@test
@params([
    (['publish', EXAMPLE_PATH, '-d', WORDS_PATH],),
    (['deploy'],),
])
def an_sftp_failure_is_an_error(argv):
    fake = RefusingSftp()
    code, out, err = run(argv + ['--remote', 'host:/srv/x'], run_batch=fake)
    assert code == 1
    assert out == ''
    assert err == 'error: Connection refused\n'


@test
def deploy_uploads_the_site():
    fake = FakeSftp()
    code, out, err = run(['deploy', '--remote', 'host:/srv/x'],
                         run_batch=fake)
    assert code == 0
    assert out == 'deployed to host:/srv/x\n'
    assert len(fake.calls) == 1
    assert '/srv/x/index.html' in fake.uploaded


@test
def a_bug_keeps_its_traceback():
    def broken(host, commands):
        raise ValueError('a programming error')

    with catch_exceptions() as caught:
        run(['deploy', '--remote', 'host:/srv/x'], run_batch=broken)
    assert len(caught) == 1
    assert isinstance(caught[0], ValueError)


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
