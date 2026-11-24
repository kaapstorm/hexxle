from hexxle.core.paths import MIN_WORD_LENGTH, find_paths

# One letter: a tap on a tile, not an attempt at a word.
SINGLE_LETTER = 'single_letter'
TOO_SHORT = 'too_short'
FOUND = 'found'
BONUS = 'bonus'
ALREADY = 'already'
NOT_A_WORD = 'not_a_word'


def _bump(counts, pos, step):
    counts[pos] = counts.get(pos, 0) + step


class Game:
    def __init__(self, puzzle, found=()):
        self.puzzle = puzzle
        self.required = set(puzzle.required)
        self.bonus = set(puzzle.bonus) - self.required
        self.found = set()
        # Per required word: the tiles some path starts on, and the tiles
        # some path uses. Computed once; counts are kept up to date.
        self._starts = {}
        self._uses = {}
        self._start_counts = {}
        self._use_counts = {}
        for word in self.required:
            paths = find_paths(puzzle.board, word)
            starts = set(path[0] for path in paths)
            uses = set()
            for path in paths:
                uses.update(path)
            self._starts[word] = starts
            self._uses[word] = uses
            self._adjust(word, 1)
        for word in found:
            if word in self.required or word in self.bonus:
                self._add(word)

    def _adjust(self, word, step):
        for pos in self._starts[word]:
            _bump(self._start_counts, pos, step)
        for pos in self._uses[word]:
            _bump(self._use_counts, pos, step)

    def _add(self, word):
        if word in self.found:
            return
        self.found.add(word)
        if word in self.required:
            self._adjust(word, -1)

    def submit(self, word):
        if len(word) < 2:
            return SINGLE_LETTER
        if len(word) < MIN_WORD_LENGTH:
            return TOO_SHORT
        if word in self.found:
            return ALREADY
        if word in self.required:
            self._add(word)
            return FOUND
        if word in self.bonus:
            self._add(word)
            return BONUS
        return NOT_A_WORD

    def found_words(self):
        return sorted(self.found)

    def found_groups(self):
        words = sorted(
            (word for word in self.found if word in self.required),
            key=lambda word: (len(word), word))
        groups = []
        for word in words:
            if groups and groups[-1][0] == len(word):
                groups[-1][1].append(word)
            else:
                groups.append((len(word), [word]))
        return groups

    def found_bonus(self):
        return sorted(word for word in self.found if word in self.bonus)

    def progress(self):
        required_found = len(self.found & self.required)
        return (required_found, len(self.required),
                len(self.found) - required_found)

    def is_complete(self):
        return self.required <= self.found

    def hints(self, pos):
        return (self._start_counts.get(pos, 0),
                self._use_counts.get(pos, 0))

    def is_dimmed(self, pos):
        return self.hints(pos) == (0, 0)
