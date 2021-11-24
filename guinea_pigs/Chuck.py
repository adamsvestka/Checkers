import random
from guinea_pigs.oasis import *
from checkers import *


class Chuck(Player):
    """
    In the shadows I have seen thee, O Alfred!
    """

    def __init__(self, color: ColorPalette, direction: bool, id: int):
        super().__init__(color, direction, id)

        self.animating_piece: Optional[Piece] = None

    def get_animating_piece(self, game: Game):
        if game.no_gui:
            return

        if self.animating_piece is not None:
            if self.animating_piece.animation_progress == 1 and self.animating_piece.animation_from is self.animating_piece.tile:
                self.animating_piece = None
            else:
                return self.animating_piece

        for player in game.players:
            if player is self:
                continue
            for piece in player.pieces:
                if piece.animation_progress < 1:
                    self.animating_piece = piece
                    return self.animating_piece

    def run(self, game: Game):
        if self.get_animating_piece(game) is not None:
            return

        else:
            moves = [piece for piece, move in self.moves.items() if len(move) > 0]

            best = (-1, None, None)
            for piece in moves:
                for move in self.moves[piece]:
                    vg = VirtualGame(piece, move, game)
                    score = vg.players[self.id].calculateScore()
                    # vg.draw()
                    # vg.draw()
                    # vg.screenshot(f"screenshot")
                    if not game.no_gui:
                        print(score)
                    if score > best[0]:
                        best = (score, piece, move)

            piece, move = best[1:]
            self.animating_piece = piece
            if piece.moveTo(move, game):
                self.locked_piece = piece
                self.moves = self.get_possible_moves(game)
                return

        game.nextTurn()

    def calculateScore(self):
        def d(piece: Piece):
            x = piece.tile.x
            s = Tile.Count - 1
            y = piece.tile.y if piece.player.direction_down else s - piece.tile.y
            c = len(self.pieces)
            return (
                + 200
                + random.randint(0, 50)
            ) if piece.is_king and c > Game.InitialPieces * 0.5 else (
                + 200
                - pow(y - s / 2, 2)
                - pow(x - s / 2, 2)
                + random.randint(0, 5)
            ) if piece.is_king else (
                + pow(y, 0.5) * 10
                + 100 if y == 0 or y == s else 0
                + 50 - y if x == 0 or x == s else 0
            ) if c > Game.InitialPieces * 0.5 else (
                + y * 10
                + 10 if x == 0 or x == s else 0
            )

        top = 10000
        return sum(d(piece) for piece in self.pieces) / top
