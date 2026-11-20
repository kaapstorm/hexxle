"""Where the test fixture files are."""

from hexxle.repo import REPO

FIXTURES = REPO / 'tests' / 'fixtures'
# A directory of good puzzles, the newest being the example puzzle.
PUZZLES = FIXTURES / 'puzzles'
EXAMPLE_PATH = PUZZLES / '2026-11-20.txt'
