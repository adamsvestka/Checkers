import random
from typing import Optional

from checkers import *


class Chuck(Player):
    def __init__(self, name, color):
        super().__init__(name, color)

        self.animating_piece: Optional[Piece] = None

    def get_animating_piece(self, game: Game):
        if self.animating_piece is not None:
            if self.animating_piece.animation_progress == 1:
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
        if len(self.moves) == 0:
            print("No moves")

        elif self.get_animating_piece(game) is not None:
            return

        else:
            moves = [piece for piece, move in self.moves.items() if len(move) > 0]
            piece = random.choice(list(moves))
            piece.moveTo(random.choice(self.moves[piece]), game)
            self.animating_piece = piece

        game.nextTurn()
