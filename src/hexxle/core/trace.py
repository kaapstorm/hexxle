class Trace:
    """The path of tiles being dragged through."""

    def __init__(self, board):
        self._board = board
        self.path = []
        self.armed = False

    def start(self, pos):
        self.path = [pos]

    def move_to(self, pos):
        if not self.path:
            return False
        if len(self.path) >= 2 and pos == self.path[-2]:
            self.path.pop()
            return True
        if pos in self.path or pos not in self._board:
            return False
        if pos not in self._board.neighbours(self.path[-1]):
            return False
        self.path.append(pos)
        return True

    def set_armed(self, flag):
        self.armed = flag

    def word(self):
        return ''.join(self._board.letter(pos) for pos in self.path)

    def finish(self):
        word = None if self.armed or not self.path else self.word()
        self.cancel()
        return word

    def cancel(self):
        self.path = []
        self.armed = False
