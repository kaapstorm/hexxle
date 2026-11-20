import json
import shlex
import tempfile
from pathlib import Path

from testsweet import catch_exceptions, params, test

from hexxle.dictionary import load_dictionary
from hexxle.errors import HexxleError
from hexxle.publish import PublishError, deploy, publish
from hexxle.sftp import SftpError
from tests.core.examples import EXAMPLE
from tests.fixture_paths import EXAMPLE_PATH, WORDS_PATH
from tests.tool.fake_sftp import FailingSecondCall, FakeSftp

WORDS = load_dictionary(WORDS_PATH)


@test
def publishes_the_puzzle_and_a_new_index():
    fake = FakeSftp('/srv/x/puzzles/2026-11-18.txt\n'
                    '/srv/x/puzzles/index.json\n')
    publish(EXAMPLE_PATH, 'host:/srv/x', WORDS, run_batch=fake)
    assert fake.uploaded['/srv/x/puzzles/2026-11-20.txt'] == EXAMPLE
    index = json.loads(fake.uploaded['/srv/x/puzzles/index.json'])
    assert index == ['2026-11-20', '2026-11-18']
    assert all(host == 'host' for host, _ in fake.calls)
    assert len(fake.calls) == 2
    assert fake.calls[0][1] == ['-mkdir "/srv/x"', '-mkdir "/srv/x/puzzles"',
                                'ls -1 "/srv/x/puzzles"']


@test
def works_with_a_remote_relative_to_the_login_directory():
    fake = FakeSftp()
    publish(EXAMPLE_PATH, 'me@host:sites/hexxle', WORDS, run_batch=fake)
    assert 'sites/hexxle/puzzles/2026-11-20.txt' in fake.uploaded
    assert fake.calls[0][0] == 'me@host'


@test
def returns_warnings():
    fake = FakeSftp()
    warnings = publish(EXAMPLE_PATH, 'host:/srv/x', WORDS, run_batch=fake)
    assert len(warnings) == 2
    assert any('ACED' in line for line in warnings)
    assert any('AXED' in line for line in warnings)


@test
def refuses_a_puzzle_with_errors_before_touching_the_server():
    fake = FakeSftp()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / '2026-11-20.txt'
        path.write_text(EXAMPLE.replace('TAXI', 'TAXIS'))
        with catch_exceptions() as caught:
            publish(path, 'host:/srv/x', WORDS, run_batch=fake)
    assert len(caught) == 1
    assert isinstance(caught[0], PublishError)
    errors = caught[0].errors
    assert any('TAXIS' in message for message in errors)
    assert fake.calls == []


@test
def refuses_to_replace_a_published_puzzle():
    fake = FakeSftp('/srv/x/puzzles/2026-11-20.txt\n')
    with catch_exceptions() as caught:
        publish(EXAMPLE_PATH, 'host:/srv/x', WORDS, run_batch=fake)
    assert len(caught) == 1
    assert isinstance(caught[0], PublishError)
    errors = caught[0].errors
    assert '2026-11-20' in ' '.join(errors)
    assert fake.uploaded == {}


@test
def replaces_with_force():
    fake = FakeSftp('/srv/x/puzzles/2026-11-20.txt\n'
                    '/srv/x/puzzles/2026-11-18.txt\n')
    publish(EXAMPLE_PATH, 'host:/srv/x', WORDS, force=True,
            run_batch=fake)
    assert fake.uploaded['/srv/x/puzzles/2026-11-20.txt'] == EXAMPLE
    index = json.loads(fake.uploaded['/srv/x/puzzles/index.json'])
    assert index == ['2026-11-20', '2026-11-18']


@test
def says_so_when_the_index_upload_fails_after_the_puzzle_went_up():
    fake = FailingSecondCall()
    with catch_exceptions() as caught:
        publish(EXAMPLE_PATH, 'host:/srv/x', WORDS, run_batch=fake)
    assert len(caught) == 1
    assert isinstance(caught[0], SftpError)
    message = str(caught[0])
    assert '2026-11-20' in message
    assert '--force' in message
    assert 'connection lost' in message


@test
def deploys_the_site_and_never_touches_puzzles():
    fake = FakeSftp()
    deploy('host:/srv/x', run_batch=fake)
    for path in ('/srv/x/index.html', '/srv/x/storage.js',
                 '/srv/x/hexxle/core/board.py',
                 '/srv/x/pyscript/core.js',
                 '/srv/x/micropython/micropython.wasm'):
        assert path in fake.uploaded, path
    assert len(fake.calls) == 1
    commands = fake.calls[0][1]
    assert not any('puzzles' in command for command in commands)
    for path in fake.uploaded:
        relative = path[len('/srv/x/'):]
        assert not relative.startswith('tests'), path
        for name in ('tests.html', 'run_tests.py', 'testsweet.py'):
            assert relative.split('/')[-1] != name, path
    # parents are created before their children
    made = [shlex.split(c)[1] for c in commands if c.startswith('-mkdir ')]
    assert made[0] == '/srv/x'
    for path in made:
        parent = path.rsplit('/', 1)[0]
        if parent != '/srv':
            assert parent in made[:made.index(path)], path


@test
@params([
    (lambda fake: publish(EXAMPLE_PATH, 'host:/srv/x\nrm y', WORDS,
                          run_batch=fake),),
    (lambda fake: deploy('host:/srv/x\nrm y', run_batch=fake),),
])
def a_remote_with_a_newline_sends_nothing(action):
    fake = FakeSftp()
    with catch_exceptions() as caught:
        action(fake)
    assert len(caught) == 1
    assert isinstance(caught[0], HexxleError)
    assert fake.calls == []
