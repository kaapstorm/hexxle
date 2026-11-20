"""Stand-ins for ``hexxle.sftp.run_sftp_batch``; nothing is sent."""

import shlex
from pathlib import Path

from hexxle.sftp import SftpError


class FakeSftp:
    def __init__(self, listing=''):
        self.listing = listing
        self.calls = []       # (host, commands)
        self.uploaded = {}    # remote path -> file text, read at call time

    def __call__(self, host, commands):
        self.calls.append((host, list(commands)))
        for command in commands:
            if command.startswith('put '):
                _, local, remote = shlex.split(command)
                self.uploaded[remote] = Path(local).read_bytes().decode(
                    'utf-8', errors='replace')
        if any(command.startswith('ls ') for command in commands):
            return self.listing
        return ''


class FailingSecondCall(FakeSftp):
    def __call__(self, host, commands):
        if self.calls:
            raise SftpError('connection lost')
        return super().__call__(host, commands)


class RefusingSftp(FakeSftp):
    """Fails every batch, as sftp does when it cannot connect."""

    def __call__(self, host, commands):
        self.calls.append((host, list(commands)))
        raise SftpError('Connection refused')
