import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from testsweet import catch_exceptions, params, test

from hexxle.errors import HexxleError
from hexxle.sftp import (
    SftpError,
    parse_listing,
    quote,
    run_sftp_batch,
    split_remote,
)

# A stand-in for sftp: records its arguments and standard input beside
# itself, then prints a listing, or fails like an unreachable host.
FAKE_SFTP = """#!/bin/sh
here=$(dirname "$0")
printf '%s\\n' "$@" > "$here/argv"
cat > "$here/stdin"
if [ -e "$here/fail" ]; then
  echo 'ssh: connect to host example: Connection refused' >&2
  exit 255
fi
echo '/srv/x/puzzles/index.json'
"""


@contextmanager
def search_path(value: str) -> Iterator[None]:
    """Run the block with ``PATH`` set to ``value``."""
    previous = os.environ.get('PATH')
    os.environ['PATH'] = value
    try:
        yield
    finally:
        if previous is None:
            del os.environ['PATH']
        else:
            os.environ['PATH'] = previous


@contextmanager
def fake_sftp(fail: bool = False) -> Iterator[Path]:
    """Put a fake ``sftp`` first on ``PATH``; yield its directory."""
    with tempfile.TemporaryDirectory() as tmp:
        bin_dir = Path(tmp)
        script = bin_dir / 'sftp'
        script.write_text(FAKE_SFTP)
        script.chmod(0o755)
        if fail:
            (bin_dir / 'fail').touch()
        with search_path(
            str(bin_dir) + os.pathsep + os.environ.get('PATH', ''),
        ):
            # Never let a test reach the real sftp.
            found = shutil.which('sftp')
            assert found == str(script), found
            yield bin_dir


@test
def runs_sftp_in_batch_mode_with_the_commands_on_stdin():
    with fake_sftp() as bin_dir:
        output = run_sftp_batch('me@host', ['-mkdir "/srv/x"', 'ls -1 "/x"'])
        argv = (bin_dir / 'argv').read_text().splitlines()
        stdin = (bin_dir / 'stdin').read_text()
    assert argv == ['-b', '-', '--', 'me@host']
    assert stdin == '-mkdir "/srv/x"\nls -1 "/x"\n'
    assert output == '/srv/x/puzzles/index.json\n'


@test
def a_failing_sftp_raises_with_its_error_output():
    with fake_sftp(fail=True):
        with catch_exceptions() as caught:
            run_sftp_batch('host', ['ls'])
    assert len(caught) == 1
    assert isinstance(caught[0], SftpError)
    message = str(caught[0])
    assert message == 'ssh: connect to host example: Connection refused'


@test
def a_missing_sftp_raises():
    with tempfile.TemporaryDirectory() as tmp:
        with search_path(tmp):
            with catch_exceptions() as caught:
                run_sftp_batch('host', ['ls'])
    assert len(caught) == 1
    assert isinstance(caught[0], SftpError)
    message = str(caught[0])
    assert message == 'sftp is not installed'


@test
@params([
    ('host:/srv/x/', ('host', '/srv/x')),
    ('me@host:sites/hexxle', ('me@host', 'sites/hexxle')),
])
def splits_remotes(remote, expected):
    assert split_remote(remote) == expected


@test
@params([('host',), (':/srv',), ('host:',), ('-oProxyCommand=x:path',)])
def rejects_bad_remotes(remote):
    with catch_exceptions() as caught:
        split_remote(remote)
    assert len(caught) == 1
    assert isinstance(caught[0], HexxleError)


@test
def quotes_paths():
    quoted = quote('/srv/my "site"')
    assert quoted == '"/srv/my \\"site\\""'


@test
@params([
    ('a\\b',), ('a\nb',), ('a\rb',),
    ('/srv/*',), ('/srv/x?',), ('/srv/drafts[old]',), ('-x',),
])
def refuses_unquotable_characters(path):
    with catch_exceptions() as caught:
        quote(path)
    assert len(caught) == 1
    assert isinstance(caught[0], HexxleError)


@test
def parses_a_listing():
    output = ('sftp> -mkdir "/srv/x/puzzles"\n'
              'sftp> ls -1 "/srv/x/puzzles"\n'
              '/srv/x/puzzles/2026-11-18.txt\n'
              '/srv/x/puzzles/index.json\n\n')
    names = parse_listing(output)
    assert names == ['2026-11-18.txt', 'index.json']
