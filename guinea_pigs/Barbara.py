from guinea_pigs.oasis import *
from checkers import *


class Barbara(Player):
    """
    Always forward. Forward, always.
    """

    def __init__(self, color: ColorPalette, direction: bool):
        super().__init__(color, direction)

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
                    score = vg.players[self.uid].calculateScore()
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
            s = Tile.Count - 1
            y = piece.tile.y if piece.player.direction_down else s - piece.tile.y
            return (
                y
            )

        top = 1000  # (2 * Tile.Count - Game.InitialRows + 1) * Game.InitialRows / 2 * Tile.Count / 2
        return sum(d(piece) for piece in self.pieces) / top
