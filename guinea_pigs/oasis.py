from checkers import *


class VirtualGame(Game):
    FrameRate = 1
    AnimationDuration = 1

    def __init__(self, _piece: Piece, _move: Move, game: Game):
        self.screen = pygame.Surface((Tile.Size * Tile.Count, Tile.Size * Tile.Count))
        self.victor = None

        self.tiles: list[list[Tile]] = [[game.tiles[x][y] for y in range(Tile.Count)] for x in range(Tile.Count)]

        self.players: list[Player] = [player.copy() for player in game.players]

        self.simulate(_piece, _move)

    def simulate(self, _piece: Piece, _move: Move):
        tile1 = _piece.tile.copy()
        player1 = self.players[_piece.player.id]
        player1.pieces.remove(_piece)
        piece1 = _piece.copy(tile1, player1)

        piece2 = None
        if _move.capturing:
            tile2 = _move.captured_piece.tile.copy()
            player2 = self.players[_move.captured_piece.player.id]
            player2.pieces.remove(_move.captured_piece)
            piece2 = _move.captured_piece.copy(tile2, player2)

        tile3 = _move.target_tile.copy()
        move = Move(tile3, piece2)

        piece1.moveTo(move, self)

    def draw_debug(self):
        pass
