import random

from guinea_pigs.oasis import *
from checkers import *


class Alfred(Player):
    """
    What, where am I? What is this?!?
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

            piece = random.choice(list(moves))
            self.animating_piece = piece
            if piece.moveTo(random.choice(self.moves[piece]), game):
                self.locked_piece = piece
                self.moves = self.get_possible_moves(game)
                return

        game.nextTurn()
