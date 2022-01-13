import random
from guinea_pigs.oasis import *
from checkers import *


class Chuck(Player):
    """
    In the shadows I have seen thee, O Alfred!
    """

    def __init__(self, color: ColorPalette, direction: bool):
        super().__init__(color, direction)

        self.animating_piece: Optional[Piece] = None

        self.queue: list[Move] = []

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

    def rank_moves(self, game: Game):
        heirarchy = []

        def traverse(game: Game, move: Move, previous: list[Move]):
            vg = VirtualGame(game)
            this = vg.get_player(self)
            if moves := vg.simulate(piece, move):
                vg.active_player.locked_piece = piece
                for move in moves:
                    traverse(vg, move, previous + [move])
            else:
                score = this.calculateScore()
                heirarchy.append((score, piece, previous))

        for piece, moves in self.moves.items():
            for move in moves:
                traverse(game, move, [move])

        heirarchy.sort(key=lambda x: x[0], reverse=True)
        return heirarchy[0][1:]

    def run(self, game: Game):
        if self.get_animating_piece(game) is not None:
            return

        else:
            if not self.queue:
                self.locked_piece, self.queue = self.rank_moves(game)

            move = self.queue.pop(0)
            move.captured_piece = next(p for p in game.other_player(self).pieces if p.uid == move.captured_piece.uid) if move.captured_piece else None

            self.animating_piece = self.locked_piece
            self.locked_piece.moveTo(move, game)

            if self.queue:
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
