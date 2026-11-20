"""Draw the board in ``svg#board`` and let a finger trace words on it.

All rules live in ``hexxle.core``; this module only turns pointer events
into ``Trace`` calls and reflects the trace in the page. A pointer move
is the hot path, so it touches the DOM only when the trace changes.
"""

from pyscript import document
from pyscript.ffi import create_proxy, is_none

from hexxle.core.geometry import board_box, hex_corners, tile_at, tile_centre
from hexxle.core.trace import Trace

# SVG units per tile (hexagon circumradius); the viewBox scales them.
TILE_SIZE = 50
# The drawn hexagon is a little smaller than its cell, leaving a gap.
DRAWN_RATIO = 0.93
LETTER_RATIO = 0.8
TRACE_WIDTH_RATIO = 0.3
# Room around the board so tile edges are not clipped.
MARGIN = 3


def _pos_key(pos):
    return '%d,%d' % pos


def _point(x, y):
    return '%.1f,%.1f' % (x, y)


class BoardView:
    def __init__(self, board, on_submit):
        self._board = board
        self._on_submit = on_submit
        self._trace = Trace(board)
        self._svg = document.querySelector('svg#board')
        self._word = document.querySelector('#word')
        self._draw()
        self._line = self._svg.querySelector('#trace-line')
        self._tiles = {}
        self._points = {}
        for pos in board.positions():
            self._tiles[pos] = self._svg.querySelector(
                'g.tile[data-pos="%s"]' % _pos_key(pos))
            self._points[pos] = _point(*tile_centre(pos, TILE_SIZE))
        self._shown = []
        self._pointer = None
        self._to_svg = None
        self._top = 0
        self._handlers = [
            ('pointerdown', create_proxy(self._on_down)),
            ('pointermove', create_proxy(self._on_move)),
            ('pointerup', create_proxy(self._on_up)),
            ('pointercancel', create_proxy(self._on_cancel)),
            # Capture can also be lost without a pointerup (for example
            # to a context menu); treat that like a cancel.
            ('lostpointercapture', create_proxy(self._on_cancel)),
        ]
        for kind, handler in self._handlers:
            self._svg.addEventListener(kind, handler)

    def _draw(self):
        min_x, min_y, width, height = board_box(self._board, TILE_SIZE)
        min_x -= MARGIN
        min_y -= MARGIN
        width += 2 * MARGIN
        height += 2 * MARGIN
        self._svg.setAttribute(
            'viewBox', '%.1f %.1f %.1f %.1f' % (min_x, min_y, width, height))
        self._svg.style.setProperty('--aspect', '%.4f' % (width / height))

        parts = []
        drawn = TILE_SIZE * DRAWN_RATIO
        for pos in self._board.positions():
            cx, cy = tile_centre(pos, TILE_SIZE)
            corners = ' '.join(
                _point(x, y) for x, y in hex_corners(cx, cy, drawn))
            parts.append(
                '<g class="tile" data-pos="%s">'
                '<polygon points="%s"></polygon>'
                '<text x="%.1f" y="%.1f" font-size="%.1f">%s</text>'
                '</g>' % (
                    _pos_key(pos), corners, cx, cy,
                    TILE_SIZE * LETTER_RATIO, self._board.letter(pos)))
        parts.append(
            '<polyline id="trace-line" points="" stroke-width="%.1f">'
            '</polyline>' % (TILE_SIZE * TRACE_WIDTH_RATIO))
        self._svg.innerHTML = ''.join(parts)

    def _on_down(self, event):
        if self._pointer is not None:
            return
        if not event.isPrimary or event.button != 0:
            return
        group = event.target.closest('g.tile')
        if is_none(group):
            return
        column, row = group.getAttribute('data-pos').split(',')
        self._pointer = event.pointerId
        self._svg.setPointerCapture(self._pointer)
        # The page cannot scroll or resize mid-trace, so the mapping from
        # screen to SVG units is fetched once here, not on every move.
        matrix = self._svg.getScreenCTM().inverse()
        self._to_svg = (
            matrix.a, matrix.b, matrix.c, matrix.d, matrix.e, matrix.f)
        self._top = self._svg.getBoundingClientRect().top
        self._trace.start((int(column), int(row)))
        self._show()

    def _on_move(self, event):
        if self._pointer is None or event.pointerId != self._pointer:
            return
        screen_x = event.clientX
        screen_y = event.clientY
        armed = screen_y < self._top
        if armed != self._trace.armed:
            self._trace.set_armed(armed)
            self._word.classList.toggle('cancelling', armed)
        a, b, c, d, e, f = self._to_svg
        x = a * screen_x + c * screen_y + e
        y = b * screen_x + d * screen_y + f
        pos = tile_at(self._board, x, y, TILE_SIZE)
        if pos is None or pos == self._trace.path[-1]:
            return
        if self._trace.move_to(pos):
            self._show()

    def _on_up(self, event):
        if self._pointer is None or event.pointerId != self._pointer:
            return
        word = self._trace.finish()
        self._end()
        if word:
            self._on_submit(word)

    def _on_cancel(self, event):
        if self._pointer is None or event.pointerId != self._pointer:
            return
        self._trace.cancel()
        self._end()

    def _end(self):
        self._pointer = None
        self._word.classList.remove('cancelling')
        self._show()

    def _show(self):
        """Bring the page in line with the trace, touching only changes."""
        path = list(self._trace.path)
        shown = self._shown
        same = 0
        limit = min(len(path), len(shown))
        while same < limit and path[same] == shown[same]:
            same += 1
        for pos in shown[same:]:
            self._tiles[pos].classList.remove('in-path')
        for pos in path[same:]:
            self._tiles[pos].classList.add('in-path')
        self._word.textContent = self._trace.word()
        self._line.setAttribute(
            'points', ' '.join(self._points[pos] for pos in path))
        self._shown = path
