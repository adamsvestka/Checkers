import unittest

from checkers import Player, Board, vec2
from computer import run

BOARD1 = (
    # 1234567
    " . 2 . ."  # 0
    ". . 1 . "  # 1
    " . . . ."  # 2
    ". . 1 . "  # 3
    " . . . ."  # 4
    ". . . . "  # 5
    " . . . ."  # 6
    ". . . . "  # 7
)


class AITest(unittest.TestCase):
    def test_compound_jump(self):
        compute = run(Board(BOARD1), Player.TWO)
        self.assertGreater(compute.achievable_score, 1000)

        self.assertListEqual(compute.compound_move, [
            (vec2(3, 0), vec2(5, 2)),
            (vec2(5, 2), vec2(3, 4)),
        ])
