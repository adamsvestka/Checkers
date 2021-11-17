from __future__ import annotations
import pygame


COLOR_BLACK = pygame.Color(0x21, 0x21, 0x21)
COLOR_WHITE = pygame.Color(0xfa, 0xfa, 0xfa)


class ColorPalette:
    def __init__(self, p, pl, pd, s=None, sl=None, sd=None):
        def parse_color(string):
            if string:
                return pygame.Color(int(string[1:3], 16), int(string[3:5], 16), int(string[5:7], 16))
            else:
                return pygame.Color(0, 0, 0)
        self.primary = parse_color(p)
        self.primary_light = parse_color(pl)
        self.primary_dark = parse_color(pd)
        self.secondary = parse_color(s)
        self.secondary_light = parse_color(sl)
        self.secondary_dark = parse_color(sd)


class Tile:
    Size = 100
    Count = 8

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.piece: Piece = None

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Tile):
            return self.x == o.x and self.y == o.y
        return False

    def draw(self, screen: pygame.Surface):
        self.rect = pygame.draw.rect(screen, COLOR_WHITE, (self.x * Tile.Size, self.y * Tile.Size, Tile.Size, Tile.Size))


class Move:
    def __init__(self, tile: Tile, target: Piece = None):
        self.target_tile = tile
        if target is not None:
            self.captured_piece: Piece = target
            self.capturing = True
        else:
            self.captured_piece = None
            self.capturing = False


class Piece:
    Size = Tile.Size * 0.45

    def __init__(self, tile: Tile, player: Player):
        self.tile: Tile = tile
        self.is_selected = False
        self.tile.piece = self
        self.player = player
        self.is_king = False
        self.animation_from: Tile = tile
        self.animation_progress = 1

    def __hash__(self):
        return hash((self.tile.x, self.tile.y))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Piece):
            return self.tile == o.tile
        return False

    def moveTo(self, move: Move, game: Game):
        """
        Execute a move, automatically capturing if necessary.

        Returns True if further captures are possible, otherwise False.
        """
        self.tile.piece = None
        self.tile = move.target_tile
        self.animation_progress = 0
        self.tile.piece = self

        if self.tile.y == (Tile.Count - 1 if self.player.direction_down else 0):
            self.is_king = True
            if move.capturing:
                move.captured_piece.capture()
            return False

        if move.capturing:
            move.captured_piece.capture()
            for move in self.getPossibleMoves(game):
                if move.capturing:
                    return True

        return False

    def getPossibleMoves(self, game: Game):
        if self.player.locked_piece is not None and self.player.locked_piece is not self:
            return

        x, y = self.tile.x, self.tile.y
        dir = 1 if self.player.direction_down else -1

        def get_diagonal_tile(dx, dy):
            tile = game.getTileAt(x + dx, y + dy)
            if tile:
                if tile.piece:
                    if tile.piece.player is not self.player:
                        tile2 = game.getTileAt(x + 2 * dx, y + 2 * dy)
                        if tile2 and not tile2.piece:
                            return Move(tile2, tile.piece)
                else:
                    return Move(tile)

        tile = get_diagonal_tile(1, dir)
        if tile:
            yield tile
        tile = get_diagonal_tile(-1, dir)
        if tile:
            yield tile

        if self.is_king:
            tile = get_diagonal_tile(1, -dir)
            if tile:
                yield tile
            tile = get_diagonal_tile(-1, -dir)
            if tile:
                yield tile

    def capture(self):
        self.player.pieces.remove(self)
        self.tile.piece = None

    def draw(self, screen: pygame.Surface, moves: list[Move] = None):
        pos_x = self.animation_from.x * (1 - self.animation_progress) + self.tile.x * self.animation_progress
        pos_y = self.animation_from.y * (1 - self.animation_progress) + self.tile.y * self.animation_progress

        if self.animation_progress < 1:
            self.animation_progress = min(self.animation_progress + 1000 / Game.Framerate / Game.AnimationDuration, 1)
        else:
            self.animation_from = self.tile

        def draw_piece(x, y, color, radius=self.Size):
            if self.is_king:
                z = Tile.Size // 20
                a = z * 4
                b = z * 5
                c = Tile.Size - b
                d = b - a
                e = Tile.Size - 2 * d
                f = Tile.Size - 2 * b

                pygame.draw.circle(screen, color, (x * Tile.Size + b, y * Tile.Size + b), a)
                pygame.draw.circle(screen, color, (x * Tile.Size + c, y * Tile.Size + b), a)
                pygame.draw.circle(screen, color, (x * Tile.Size + c, y * Tile.Size + c), a)
                pygame.draw.circle(screen, color, (x * Tile.Size + b, y * Tile.Size + c), a)
                pygame.draw.rect(screen, color, (x * Tile.Size + b, y * Tile.Size + d, f, e))
                pygame.draw.rect(screen, color, (x * Tile.Size + d, y * Tile.Size + b, e, f))
            else:
                pygame.draw.circle(screen, color, ((x + 0.5) * Tile.Size, (y + 0.5) * Tile.Size), radius)

        def draw_shadow():
            draw_piece(pos_x - 0.01, pos_y - 0.01, COLOR_BLACK)

        if not self.player.is_active or not moves:
            draw_piece(pos_x, pos_y, self.player.color_palette.primary_dark)

        elif self.is_selected:
            draw_shadow()
            draw_piece(pos_x + 0.1, pos_y + 0.1, self.player.color_palette.primary_light, self.Size + 1)
            if moves:
                for move in moves:
                    draw_piece(move.target_tile.x, move.target_tile.y, self.player.color_palette.secondary)
                    # pygame.draw.rect(game.screen, self.player.color.secondary, (move.tile.x * Tile.size, move.tile.y * Tile.size, Tile.size, Tile.size))

        else:
            draw_piece(pos_x, pos_y, self.player.color_palette.primary)


class Player:
    def __init__(self, color: ColorPalette, direction: bool):
        self.color_palette = color
        self.pieces: list[Piece] = []
        self.direction_down = direction
        self.is_active = False
        self.moves: dict[Piece, list[Move]] = None
        self.locked_piece: Piece = None

    def get_possible_moves(self, game: Game):
        moves: dict[Piece, list[Move]] = {}
        capturing = False
        for piece in self.pieces:
            moves[piece] = []
            for move in piece.getPossibleMoves(game):
                if not capturing and move.capturing:
                    capturing = True
                    for piece in moves:
                        moves[piece] = [move for move in moves[piece] if move.capturing]

                if not capturing or move.capturing:
                    moves[piece].append(move)

        return moves

    def onClick(self, tile: Tile, game: Game):
        pass

    def draw(self, screen: pygame.Surface):
        for piece in self.pieces:
            piece.draw(screen)

    def onTurnBegin(self, game: Game):
        self.is_active = True
        self.moves = self.get_possible_moves(game)

    def run(self, game: Game):
        pass

    def onTurnEnd(self, game: Game):
        self.is_active = False
        self.moves = None
        self.locked_piece = None


class Game:
    Framerate = 60
    AnimationDuration = 200

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Checkers")
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((Tile.Count * Tile.Size, Tile.Count * Tile.Size))

        self.tiles: list[list[Tile]] = [[Tile(x, y) if (x + y) % 2 else None for y in range(Tile.Count)] for x in range(Tile.Count)]

        self.players: list[Player] = []

    def setPlayers(self, Player1: function, Player2: function, colors: list[ColorPalette]):
        self.players = [
            Player1(colors[0], False),
            Player2(colors[1], True)
        ]

        for x in range(Tile.Count):
            for y in range(Tile.Count - 3, Tile.Count):
                if self.tiles[x][y]:
                    self.players[0].pieces.append(Piece(self.tiles[x][y], self.players[0]))
            for y in range(3):
                if self.tiles[x][y]:
                    self.players[1].pieces.append(Piece(self.tiles[x][y], self.players[1]))

        self.active_player = self.players[-1]

        self.nextTurn()

    def getTiles(self):
        return (tile for row in self.tiles for tile in row if tile)

    def getTileAt(self, x, y):
        if x < 0 or x >= Tile.Count or y < 0 or y >= Tile.Count:
            return None
        return self.tiles[x][y]

    def nextTurn(self):
        self.active_player.onTurnEnd(self)

        self.active_player = self.players[(self.players.index(self.active_player) + 1) % len(self.players)]

        self.active_player.onTurnBegin(self)

    def draw(self):
        self.screen.fill(COLOR_BLACK)

        for tile in self.getTiles():
            tile.draw(self.screen)
        for player in self.players:
            player.draw(self.screen)

        pygame.display.update()

    def run(self):
        self.clock.tick(self.Framerate)
        self.active_player.run(self)

    def click(self, pos: pygame.math.Vector2):
        for tile in self.getTiles():
            if tile.rect.collidepoint(pos):
                self.active_player.onClick(tile, self)
