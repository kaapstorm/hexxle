NEIGHBOUR_OFFSETS = [(-2, 0), (2, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]


class PuzzleError(Exception):
    def __init__(self, message, line=None, column=None):
        # MicroPython's Exception has no __init__ to call directly.
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self):
        if self.line is None:
            return self.message
        if self.column is None:
            return 'line %d: %s' % (self.line, self.message)
        return 'line %d, column %d: %s' % (
            self.line, self.column, self.message)


class Board:
    """Hex tiles keyed by ``(column, row)``; see ``parse_board``."""

    def __init__(self, tiles):
        self._tiles = tiles

    def letter(self, pos):
        return self._tiles[pos]

    def __contains__(self, pos):
        return pos in self._tiles

    def positions(self):
        return sorted(self._tiles, key=lambda p: (p[1], p[0]))

    def neighbours(self, pos):
        column, row = pos
        found = []
        for dc, dr in NEIGHBOUR_OFFSETS:
            other = (column + dc, row + dr)
            if other in self._tiles:
                found.append(other)
        return sorted(found)

    def render(self):
        rows = []
        for row in range(max(p[1] for p in self._tiles) + 1):
            cells = [p[0] for p in self._tiles if p[1] == row]
            chars = [' '] * (max(cells) + 1 if cells else 0)
            for column in cells:
                chars[column] = self._tiles[(column, row)]
            rows.append(''.join(chars))
        return '\n'.join(rows)


def is_letter(char):
    """Whether ``char`` is an ASCII letter, a-z or A-Z.

    The one rule for what a tile, a listed word or a dictionary word may
    contain.
    """
    return 'A' <= char <= 'Z' or 'a' <= char <= 'z'


def parse_board(lines, first_line=1):
    """Parse the board section's lines into a ``Board``.

    ``first_line`` is the file line number of ``lines[0]``. Positions are
    ``(column, row)`` with the smallest column shifted to 0 and the first
    non-blank line as row 0.
    """
    lines = [line.rstrip('\r\n ') for line in lines]
    start = 0
    while start < len(lines) and not lines[start]:
        start += 1
    end = len(lines)
    while end > start and not lines[end - 1]:
        end -= 1

    raw = []
    parity = None
    for row in range(end - start):
        index = start + row
        line_no = first_line + index
        text = lines[index]
        if not text:
            raise PuzzleError('blank line inside the board', line_no)
        for column, char in enumerate(text):
            if char == ' ':
                continue
            is_gap = char == '_'
            if not (is_gap or is_letter(char)):
                raise PuzzleError(
                    'unexpected %r in the board' % char,
                    line_no, column + 1)
            if parity is None:
                parity = (column + row) % 2
            elif (column + row) % 2 != parity:
                raise PuzzleError(
                    'tile is not aligned with the hex grid',
                    line_no, column + 1)
            if is_gap:
                continue
            char = char.upper()
            raw.append((column, row, char))

    if not raw:
        raise PuzzleError('the board has no tiles')
    shift = min(column for column, _, _ in raw)
    return Board({(c - shift, r): ch for c, r, ch in raw})
