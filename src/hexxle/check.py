from pathlib import Path

from hexxle.core.board import PuzzleError
from hexxle.core.index import identifier_of
from hexxle.core.paths import find_words
from hexxle.core.puzzle import parse_puzzle, puzzle_errors


def check_puzzle(
    path: Path, dictionary: set[str],
) -> tuple[list[str], list[str]]:
    """Return ``(errors, warnings)`` for a puzzle file."""
    errors = []
    warnings = []
    if identifier_of(path.name) is None:
        errors.append(
            'file name %s must be an identifier such as 2026-11-20.txt'
            % path.name)
    try:
        puzzle = parse_puzzle(path.read_text(encoding='utf-8'))
    except PuzzleError as error:
        errors.append(str(error))
        return errors, warnings
    errors.extend(puzzle_errors(puzzle))

    listed = set(puzzle.required + puzzle.bonus)
    for word in puzzle.required + puzzle.bonus:
        if word not in dictionary:
            warnings.append('%s is not in the dictionary' % word)
    for word in sorted(find_words(puzzle.board, dictionary) - listed):
        warnings.append('%s is on the board but not listed' % word)
    return errors, warnings
