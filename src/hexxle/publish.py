"""Upload puzzles and the game itself over sftp."""

import tempfile
from collections.abc import Callable
from pathlib import Path

from hexxle.check import check_puzzle
from hexxle.core.index import INDEX_NAME, PUZZLES_DIR, dump_index, make_index
from hexxle.errors import HexxleError
from hexxle.sftp import (
    SftpError, parse_listing, quote, run_sftp_batch, split_remote,
)
from hexxle.site import build_site


BatchRunner = Callable[[str, list[str]], str]


class PublishError(HexxleError):
    """The puzzle has errors, or is already published."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__('; '.join(errors))
        self.errors = errors


def publish(
    puzzle_path: Path, remote: str, dictionary: set[str],
    force: bool = False, run_batch: BatchRunner = run_sftp_batch,
) -> list[str]:
    """Upload a puzzle and a regenerated index. Return the warnings."""
    errors, warnings = check_puzzle(puzzle_path, dictionary)
    if errors:
        raise PublishError(errors)
    host, base = split_remote(remote)
    puzzles = base + '/' + PUZZLES_DIR
    name = puzzle_path.name

    listing = run_batch(host, [
        '-mkdir ' + quote(base),
        '-mkdir ' + quote(puzzles),
        'ls -1 ' + quote(puzzles),
    ])
    existing = parse_listing(listing)
    if name in existing and not force:
        raise PublishError([
            '%s is already published; use --force to replace it'
            % puzzle_path.stem])

    index = make_index(sorted(set(existing) | {name}))
    with tempfile.TemporaryDirectory() as tmp:
        index_path = Path(tmp) / INDEX_NAME
        index_path.write_text(dump_index(index), encoding='utf-8')
        try:
            run_batch(host, [
                'put %s %s' % (quote(str(puzzle_path)),
                               quote(puzzles + '/' + name)),
                'put %s %s' % (quote(str(index_path)),
                               quote(puzzles + '/' + INDEX_NAME)),
            ])
        except SftpError as error:
            raise SftpError(
                '%s: the puzzle %s may have been uploaded but the index '
                'was not updated; run publish --force again to repair it'
                % (error, puzzle_path.stem)) from error
    return warnings


def deploy(remote: str, run_batch: BatchRunner = run_sftp_batch) -> None:
    """Upload the game (never the puzzles directory)."""
    host, base = split_remote(remote)
    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp)
        build_site(site)
        directories = sorted(
            (path for path in site.rglob('*') if path.is_dir()),
            key=lambda path: len(path.relative_to(site).parts))
        files = sorted(path for path in site.rglob('*') if path.is_file())
        commands = ['-mkdir ' + quote(base)]
        for directory in directories:
            relative = directory.relative_to(site).as_posix()
            commands.append('-mkdir ' + quote(base + '/' + relative))
        for file in files:
            relative = file.relative_to(site).as_posix()
            commands.append(
                'put %s %s' % (quote(str(file)),
                               quote(base + '/' + relative)))
        run_batch(host, commands)
