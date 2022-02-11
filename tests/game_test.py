import unittest

import itertools

from checkers import Game, Board, Player, vec2

BOARD1 = (
    # 1234567
    " . . . ."  # 0
    ". 2 1 . "  # 1
    " . 1 . ."  # 2
    ". . . . "  # 3
    " . . . ."  # 4
    ". . . . "  # 5
    " . . . ."  # 6
    ". . . . "  # 7
)


class VirtualDrawer:
    def animate(*t): return None


class VirtualGame:
    def __init__(self, board: Board):
        self.active_player = Player.ONE
        self.moves = {}
        self.board = board
        self.locked_piece = None
        self.victor = None
        self.drawer = VirtualDrawer()

    def check_win(self):
        return Game.check_win(self)

    def next_turn(self):
        return Game.next_turn(self)

    def generate_moves(self):
        return Game.generate_moves(self)


class GameTest(unittest.TestCase):
    def test_player_moves(self):
        game = VirtualGame(Board())
        Game.generate_moves(game)
        self.assertEqual(len(game.moves), 4)
        self.assertEqual(sum(map(len, game.moves.values())), 7)

        game2 = VirtualGame(Board(BOARD1))
        Game.generate_moves(game2)
        self.assertCountEqual(itertools.chain(*game2.moves.values()), {
            vec2(1, 0),
        })
        Game.next_turn(game2)
        self.assertCountEqual(itertools.chain(*game2.moves.values()), {
            vec2(4, 3),
        })

    def test_game_win(self):
        game = VirtualGame(Board(BOARD1))
        Game.generate_moves(game)
        self.assertDictEqual(game.moves, {
            vec2(3, 2): [
                vec2(1, 0)
            ]
        })

        Game.move_piece(game, vec2(3, 2), vec2(1, 0))

        self.assertEqual(game.active_player, Player.TWO)
        self.assertDictEqual(game.moves, {})
        self.assertEqual(game.victor, Player.ONE)
