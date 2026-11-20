"""The example puzzle, shared by the tests.

``tests/fixtures/puzzles/2026-11-20.txt`` holds the same text (checked
by ``tests/tool/test_fixtures.py``).
"""

EXAMPLE = """\
 T A U
S C X L
 S E I
E D C N

---
EXACT
TAXI

--- bonus
LUXE
"""

TILE_COUNT = 14

# One path through the example board for each word, as tile positions.
PATHS = {
    'EXACT': [(3, 2), (4, 1), (3, 0), (2, 1), (1, 0)],
    'TAXI': [(1, 0), (3, 0), (4, 1), (5, 2)],
    'LUXE': [(6, 1), (5, 0), (4, 1), (3, 2)],
    'ACED': [(3, 0), (2, 1), (3, 2), (2, 3)],
    'TAX': [(1, 0), (3, 0), (4, 1)],
}
