import math

HIT_RATIO = 0.8


def tile_centre(pos, size):
    column, row = pos
    return (column * size * math.sqrt(3) / 2, row * size * 1.5)


def hex_corners(cx, cy, size):
    """Six corners of a pointy-top hexagon, first at the top, clockwise."""
    corners = []
    for index in range(6):
        angle = math.radians(-90 + 60 * index)
        corners.append(
            (cx + size * math.cos(angle), cy + size * math.sin(angle)))
    return corners


def board_box(board, size):
    """``(min_x, min_y, width, height)`` enclosing every hexagon."""
    half_width = size * math.sqrt(3) / 2
    centres = [tile_centre(pos, size) for pos in board.positions()]
    min_x = min(x for x, _ in centres) - half_width
    max_x = max(x for x, _ in centres) + half_width
    min_y = min(y for _, y in centres) - size
    max_y = max(y for _, y in centres) + size
    return (min_x, min_y, max_x - min_x, max_y - min_y)


def tile_at(board, x, y, size):
    """The tile whose centre is within the hit radius of the point."""
    radius = HIT_RATIO * size * math.sqrt(3) / 2
    for pos in board.positions():
        cx, cy = tile_centre(pos, size)
        if math.sqrt((x - cx) ** 2 + (y - cy) ** 2) <= radius:
            return pos
    return None
