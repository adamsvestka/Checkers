from checkers import *


class VirtualGame(Game):
    FrameRate = 1
    AnimationDuration = 1

    def __init__(self, game: Game):
        self.screen = pygame.Surface((Tile.Size * Tile.Count, Tile.Size * Tile.Count))
        self.victor = None

        self.tiles: list[list[Tile]] = [[game.tiles[x][y].copy() if game.tiles[x][y] else None for y in range(Tile.Count)] for x in range(Tile.Count)]

        self.players: list[Player] = [player.copy() for player in game.players]

        for player in self.players:
            for piece in player.pieces.copy():
                tile = self.get_tile(piece.tile)
                copy = piece.copy(tile, player)
                tile.piece = piece
                player.pieces.remove(piece)
                player.pieces.append(copy)

        self.active_player = self.get_player(game.active_player)

    def simulate(self, _piece: Piece, _move: Move) -> bool:
        piece = self.get_piece(_piece)
        move = Move(self.get_tile(_move.target_tile), self.get_piece(_move.captured_piece) if _move.captured_piece else None)
        return piece.moveTo(move, self)

    def get_player(self, player: Player) -> Player:
        return next(p for p in self.players if p.uid == player.uid)

    def get_piece(self, piece: Piece) -> Piece:
        for player in self.players:
            for p in player.pieces:
                if p.uid == piece.uid:
                    return p
        return None

    def get_tile(self, tile: Tile) -> Tile:
        for row in self.tiles:
            for t in row:
                if t and t.uid == tile.uid:
                    return t
        return None

    def draw(self):
        pass

    def draw_debug(self):
        pass
