import unittest

import itertools

from checkers import Board, Tile, Piece, Player, vec2

START_BOARD = (
    # 1234567
    " 2 2 2 2"  # 0
    "2 2 2 2 "  # 1
    " 2 2 2 2"  # 2
    ". . . . "  # 3
    " . . . ."  # 4
    "1 1 1 1 "  # 5
    " 1 1 1 1"  # 6
    "1 1 1 1 "  # 7
)

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


class BoardTest(unittest.TestCase):
    def test_board_init(self):
        board = Board()
        self.assertEqual(board.grid, START_BOARD)

    def test_is_in_board(self):
        self.assertTrue(Board.IsInBoard(vec2(0, 0)))
        self.assertTrue(Board.IsInBoard(vec2(Tile.Count - 1, Tile.Count - 1)))
        self.assertFalse(Board.IsInBoard(vec2(-1, 0)))
        self.assertFalse(Board.IsInBoard(vec2(0, -1)))
        self.assertFalse(Board.IsInBoard(vec2(Tile.Count, 0)))
        self.assertFalse(Board.IsInBoard(vec2(0, Tile.Count)))

    def test_is_tile(self):
        self.assertFalse(Board.IsTile(vec2(0, 0)))
        self.assertTrue(Board.IsTile(vec2(0, 1)))
        self.assertTrue(Board.IsTile(vec2(1, 0)))
        self.assertFalse(Board.IsTile(vec2(1, 1)))

    def test_adjecent_tiles(self):
        self.assertCountEqual(list(Board.AdjacentTiles(vec2(0, 1))), {
            vec2(1, 0),
            vec2(1, 2),
        })
        self.assertCountEqual(list(Board.AdjacentTiles(vec2(1, 2))), {
            vec2(0, 1),
            vec2(0, 3),
            vec2(2, 1),
            vec2(2, 3),
        })

    def test_board_get_set(self):
        board = Board()
        board.set(vec2(0, 1), Tile('1'))
        tile = board.get(vec2(0, 1))
        self.assertTrue(tile.piece)
        self.assertEqual(tile.piece.player, Player.ONE)

    def test_board_copy(self):
        board = Board()
        board_copy = board.copy()
        self.assertEqual(board.grid, board_copy.grid)

    def test_tile_empty(self):
        self.assertEqual(Board().get(vec2(0, 0)), Tile.NO_TILE)

    def test_possible_moves(self):
        board = Board(START_BOARD)
        self.assertCountEqual(list(board.get_piece_moves(vec2(0, 1))), [])
        self.assertCountEqual(list(board.get_piece_moves(vec2(1, 2))), {
            (vec2(0, 3), False),
            (vec2(2, 3), False),
        })
        self.assertCountEqual(list(board.get_piece_moves(vec2(Tile.Count - 1, 2))), {
            (vec2(Tile.Count - 2, 3), False),
        })
        self.assertCountEqual(list(board.get_piece_moves(vec2(2, 5))), {
            (vec2(1, 4), False),
            (vec2(3, 4), False),
        })

    def test_possible_moves_2(self):
        board = Board(BOARD1)
        self.assertCountEqual(board.get_piece_moves(vec2(3, 2)), {
            (vec2(1, 0), True),
        })

    def test_move(self):
        board = Board(BOARD1)
        tile = vec2(3, 2)
        move, capturing = next(board.get_piece_moves(tile))
        board.move(tile, move)
        self.assertEqual(board.get(tile), Tile.EMPTY)
        self.assertEqual(board.get(vec2(2, 1)), Tile.EMPTY)
        self.assertEqual(board.get(move).piece.player, Player.ONE)

    def test_player_pieces(self):
        board = Board(START_BOARD)
        self.assertEqual(len(list(board.get_player_pieces(Player.ONE))), 12)

        board2 = Board(BOARD1)
        self.assertCountEqual(list(board2.get_player_pieces(Player.ONE)), {
            vec2(3, 2),
            vec2(4, 1),
        })
        self.assertCountEqual(list(board2.get_player_pieces(Player.TWO)), {
            vec2(2, 1),
        })


class TileTest(unittest.TestCase):
    def test_tile_player(self):
        self.assertEqual(Tile('1').piece.player, Player.ONE)
        self.assertEqual(Tile('2').piece.player, Player.TWO)
        self.assertIsNone(Tile('.').piece)
        self.assertIsNone(Tile(' ').piece)

    def test_tile_empty(self):
        self.assertNotEqual(Tile.EMPTY, Tile.NO_TILE)
        self.assertTrue(Tile.EMPTY.empty())
        self.assertFalse(Tile("1").empty())


class PieceTest(unittest.TestCase):
    def test_piece_init(self):
        self.assertEqual(Piece("1").player, Player.ONE)
        self.assertEqual(Piece("a").player, Player.ONE)
        self.assertEqual(Piece("2").player, Player.TWO)
        self.assertEqual(Piece("b").player, Player.TWO)

    def test_piece_king(self):
        self.assertFalse(Piece("1").king)
        self.assertTrue(Piece("a").king)
        self.assertFalse(Piece("2").king)
        self.assertTrue(Piece("b").king)
