MIN_WORD_LENGTH = 4


def find_paths(board, word):
    """Every path spelling ``word`` (uppercase), sorted."""
    if not word:
        return []
    found = []

    def extend(path):
        if len(path) == len(word):
            found.append(tuple(path))
            return
        wanted = word[len(path)]
        for other in board.neighbours(path[-1]):
            if other not in path and board.letter(other) == wanted:
                path.append(other)
                extend(path)
                path.pop()

    for pos in board.positions():
        if board.letter(pos) == word[0]:
            extend([pos])
    return sorted(found)


def find_words(board, words):
    """The members of ``words`` (uppercase) that have a path on ``board``."""
    letters = set(board.letter(pos) for pos in board.positions())
    candidates = set()
    prefixes = set()
    for word in words:
        if len(word) < MIN_WORD_LENGTH:
            continue
        usable = True
        for char in word:
            if char not in letters:
                usable = False
                break
        if not usable:
            continue
        candidates.add(word)
        for end in range(1, len(word) + 1):
            prefixes.add(word[:end])

    neighbours = {pos: board.neighbours(pos) for pos in board.positions()}
    found = set()

    def extend(pos, text, visited):
        if text in candidates:
            found.add(text)
        for other in neighbours[pos]:
            if other in visited:
                continue
            longer = text + board.letter(other)
            if longer in prefixes:
                visited.add(other)
                extend(other, longer, visited)
                visited.remove(other)

    for pos in neighbours:
        first = board.letter(pos)
        if first in prefixes:
            extend(pos, first, set([pos]))
    return found
