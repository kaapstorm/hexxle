"""Thin wrapper around the system ``sftp`` command in batch mode."""

import subprocess

from hexxle.errors import HexxleError

# Refused by ``quote``.
UNQUOTABLE = '\\\n\r*?['


class SftpError(HexxleError):
    """sftp is missing, or a batch failed."""


def split_remote(remote: str) -> tuple[str, str]:
    """Split ``host:path`` into ``(host, path)``, dropping a trailing slash.

    The path may be relative to the login directory.
    """
    host, separator, path = remote.partition(':')
    if host.startswith('-'):
        raise HexxleError('remote host %r must not start with "-"' % host)
    if not separator or not host:
        raise HexxleError('remote %r must look like host:path' % remote)
    if not path:
        raise HexxleError('remote %r has no path' % remote)
    return host, path.rstrip('/') or '/'


def run_sftp_batch(host: str, commands: list[str]) -> str:
    """Run ``commands`` in one ``sftp -b -`` session; return its stdout."""
    try:
        result = subprocess.run(
            ['sftp', '-b', '-', '--', host],
            input='\n'.join(commands) + '\n',
            capture_output=True, text=True,
        )
    except FileNotFoundError:
        raise SftpError('sftp is not installed') from None
    if result.returncode != 0:
        raise SftpError(
            result.stderr.strip() or 'sftp exited with %d' % result.returncode)
    return result.stdout


def quote(path: str) -> str:
    """Double-quote ``path`` for an sftp batch command.

    Inside double quotes sftp understands ``\\"`` as a quote, so quotes
    are escaped. Refused, with ``HexxleError``:

    - a backslash or a line break, which cannot be represented safely;
    - ``*``, ``?`` and ``[``, which sftp still expands as a glob inside
      quotes, so the path could name other files;
    - a leading ``-``, which ``put``, ``mkdir`` and ``ls`` would read
      as an option.
    """
    for char in UNQUOTABLE:
        if char in path:
            raise HexxleError(
                'path %r contains %r, which cannot be sent to sftp'
                % (path, char))
    if path.startswith('-'):
        raise HexxleError('path %r must not start with "-"' % path)
    return '"%s"' % path.replace('"', '\\"')


def parse_listing(output: str) -> list[str]:
    """Base names from ``ls -1`` output, without sftp's echoed commands."""
    names = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith('sftp> '):
            continue
        names.append(line.rstrip('/').rsplit('/', 1)[-1])
    return names
