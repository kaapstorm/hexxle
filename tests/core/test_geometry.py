import math

from testsweet import test

from hexxle.core.geometry import board_box, hex_corners, tile_at, tile_centre
from hexxle.core.puzzle import parse_puzzle
from tests.core.examples import EXAMPLE

BOARD = parse_puzzle(EXAMPLE).board


def close(a, b):
    return abs(a - b) < 1e-9


@test
def every_neighbour_is_the_same_distance_away():
    size = 2
    expected = size * math.sqrt(3)
    for pos in BOARD.positions():
        x, y = tile_centre(pos, size)
        for other in BOARD.neighbours(pos):
            ox, oy = tile_centre(other, size)
            distance = math.sqrt((x - ox) ** 2 + (y - oy) ** 2)
            assert close(distance, expected)


@test
def hexagon_has_six_corners_starting_at_the_top():
    corners = hex_corners(10, 10, 2)
    count = len(corners)
    top_x, top_y = corners[0]
    assert count == 6
    assert close(top_x, 10) and close(top_y, 8)


@test
def box_encloses_all_hexagons():
    size = 2
    half_width = size * math.sqrt(3) / 2
    min_x, min_y, width, height = board_box(BOARD, size)
    assert close(min_x, -half_width)
    assert close(min_y, -size)
    assert close(width, 6 * half_width + 2 * half_width)
    assert close(height, 3 * 1.5 * size + 2 * size)


@test
def point_at_a_centre_hits_that_tile():
    x, y = tile_centre((4, 1), 2)
    hit = tile_at(BOARD, x, y, 2)
    assert hit == (4, 1)


@test
def point_between_two_tiles_hits_neither():
    ax, ay = tile_centre((2, 1), 2)
    bx, by = tile_centre((4, 1), 2)
    hit = tile_at(BOARD, (ax + bx) / 2, (ay + by) / 2, 2)
    assert hit is None
