from hexxle.core.board import PuzzleError, is_letter, parse_board
from hexxle.core.paths import MIN_WORD_LENGTH, find_paths

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
DIGITS = '0123456789'
LABEL_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789_'


class Puzzle:
    def __init__(self, board, required, bonus):
        self.board = board
        self.required = required
        self.bonus = bonus


def parse_puzzle(text):
    lines = text.split('\n')
    board_end = len(lines)
    for index, line in enumerate(lines):
        if line.startswith('---'):
            board_end = index
            break
    board = parse_board(lines[:board_end], first_line=1)

    required = []
    bonus = []
    current = None
    seen = []
    for index in range(board_end, len(lines)):
        line_no = index + 1
        line = lines[index].strip()
        if line.startswith('---'):
            if line == '---':
                name = 'required'
            elif line == '--- bonus':
                name = 'bonus'
            else:
                raise PuzzleError(
                    "expected '---' or '--- bonus'", line_no)
            if name in seen:
                raise PuzzleError('repeated %s section' % name, line_no)
            if name == 'bonus' and 'required' not in seen:
                raise PuzzleError(
                    "'--- bonus' must come after '---'", line_no)
            seen.append(name)
            current = required if name == 'required' else bonus
        elif line:
            if not all(is_letter(char) for char in line):
                raise PuzzleError(
                    'word %r must contain only letters A-Z' % line,
                    line_no)
            current.append(line.upper())
    return Puzzle(board, required, bonus)


def _duplicates(words):
    found = []
    for word in words:
        if words.count(word) > 1 and word not in found:
            found.append(word)
    return found


def puzzle_errors(puzzle):
    errors = []
    if not puzzle.required:
        errors.append('no required words')
    for name, words in (('required', puzzle.required),
                        ('bonus', puzzle.bonus)):
        for word in words:
            if len(word) < MIN_WORD_LENGTH:
                errors.append(
                    '%s word %s is shorter than %d letters'
                    % (name, word, MIN_WORD_LENGTH))
            elif not find_paths(puzzle.board, word):
                errors.append(
                    '%s word %s is not on the board' % (name, word))
        for word in _duplicates(words):
            errors.append('%s word %s is listed twice' % (name, word))
    for word in _duplicates(puzzle.required + puzzle.bonus):
        if word in puzzle.required and word in puzzle.bonus:
            errors.append(
                'word %s is in both required and bonus' % word)
    return errors


def parse_identifier(ident):
    bad = ValueError('bad puzzle identifier %r' % ident)
    if len(ident) < 10:
        raise bad
    date, rest = ident[:10], ident[10:]
    for index, char in enumerate(date):
        if index in (4, 7):
            if char != '-':
                raise bad
        elif char not in DIGITS:
            raise bad
    if not 1 <= int(date[5:7]) <= 12 or not 1 <= int(date[8:10]) <= 31:
        raise bad
    if not rest:
        return date, None
    label = rest[1:]
    if rest[0] != '_' or not label:
        raise bad
    for char in label:
        if char not in LABEL_CHARS:
            raise bad
    return date, label


def describe_identifier(ident):
    date, label = parse_identifier(ident)
    year, month, day = date.split('-')
    shown = '%d %s %s' % (int(day), MONTHS[int(month) - 1], year)
    return shown, (label or '').replace('_', ' ')
