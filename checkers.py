from __future__ import annotations
from typing import Optional
import sys
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
        self.piece: Optional[Piece] = None

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Tile):
            return self.x == o.x and self.y == o.y
        return False

    def copy(self):
        tile = Tile(self.x, self.y)
        tile.piece = self.piece
        return tile

    def draw(self, game: Game):
        self.rect = pygame.draw.rect(game.screen, COLOR_WHITE, (self.x * Tile.Size, self.y * Tile.Size, Tile.Size, Tile.Size))


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
        self.tile.piece = self
        self.player = player
        self.player.pieces.append(self)
        self.is_selected = False
        self.is_king = False
        self.animation_from = tile
        self.animation_progress = 1.0

    def __hash__(self):
        return hash((self.tile.x, self.tile.y))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Piece):
            return self.tile == o.tile
        return False

    def copy(self, tile: Tile, player: Player):
        piece = Piece(tile, player)
        piece.is_king = self.is_king
        return piece

    def moveTo(self, move: Move, game: Game):
        """
        Execute a move, automatically capturing if necessary.

        Returns True if further captures are possible, otherwise False.
        """
        self.animation_from = self.tile
        self.animation_progress = 0
        self.tile.piece = None
        self.tile = move.target_tile
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

    def draw(self, game: Game, moves: list[Move] = None):
        pos_x = self.animation_from.x * (1 - self.animation_progress) + self.tile.x * self.animation_progress
        pos_y = self.animation_from.y * (1 - self.animation_progress) + self.tile.y * self.animation_progress

        if self.animation_progress < 1:
            self.animation_progress = min(self.animation_progress + 1000 / game.Framerate / game.AnimationDuration, 1)
        elif self.animation_from is not self.tile:
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

                pygame.draw.circle(game.screen, color, (x * Tile.Size + b, y * Tile.Size + b), a)
                pygame.draw.circle(game.screen, color, (x * Tile.Size + c, y * Tile.Size + b), a)
                pygame.draw.circle(game.screen, color, (x * Tile.Size + c, y * Tile.Size + c), a)
                pygame.draw.circle(game.screen, color, (x * Tile.Size + b, y * Tile.Size + c), a)
                pygame.draw.rect(game.screen, color, (x * Tile.Size + b, y * Tile.Size + d, f, e))
                pygame.draw.rect(game.screen, color, (x * Tile.Size + d, y * Tile.Size + b, e, f))
            else:
                pygame.draw.circle(game.screen, color, ((x + 0.5) * Tile.Size, (y + 0.5) * Tile.Size), radius)

        def draw_shadow():
            draw_piece(pos_x - 0.01, pos_y - 0.01, COLOR_BLACK)

        if not self.player.is_active or not moves:
            draw_piece(pos_x, pos_y, self.player.color_palette.primary_dark)

        elif self.is_selected and self.animation_from is self.tile:
            draw_shadow()
            draw_piece(pos_x + 0.1, pos_y + 0.1, self.player.color_palette.primary_light)

        else:
            draw_piece(pos_x, pos_y, self.player.color_palette.primary)

        if self.is_selected and moves:
            for move in moves:
                draw_piece(move.target_tile.x, move.target_tile.y, self.player.color_palette.secondary)


class Player:
    def __init__(self, color: ColorPalette, direction: bool, id: int):
        self.color_palette = color
        self.pieces: list[Piece] = []
        self.direction_down = direction
        self.is_active = False
        self.moves: Optional[dict[Piece, list[Move]]] = None
        self.locked_piece: Optional[Piece] = None
        self.id = id

    def copy(self):
        player = type(self)(self.color_palette, self.direction_down, self.id)
        player.pieces = self.pieces.copy()
        player.is_active = self.is_active
        return player

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

    def calculateScore(self):
        return len(self.pieces) / Game.InitialPieces

    def onClick(self, tile: Tile, game: Game):
        pass

    def draw(self, game: Game):
        for piece in self.pieces:
            piece.draw(game)

    def onTurnBegin(self, game: Game):
        self.is_active = True
        self.moves = self.get_possible_moves(game)
        if len([piece for piece, move in self.moves.items() if len(move) > 0]) == 0:
            game.victor = game.players[1 - self.id]

    def run(self, game: Game):
        pass

    def onTurnEnd(self, game: Game):
        self.is_active = False
        self.moves = None
        self.locked_piece = None


class Game:
    Framerate = 60
    AnimationDuration = 200
    FontSize = 13
    InitialRows = 3
    InitialPieces = (InitialRows * Tile.Count / 2)

    def __init__(self, noGUI: bool = False):
        self.no_gui = noGUI
        if not self.no_gui:
            pygame.init()
            pygame.font.init()

            pygame.display.set_caption("Checkers")
            self.clock = pygame.time.Clock()
            self.screen = pygame.display.set_mode((Tile.Count * Tile.Size, Tile.Count * Tile.Size))
            self.font = pygame.font.SysFont("SF Pro Display", Tile.Size)
            self.font_debug = pygame.font.SysFont("Menlo", self.FontSize)

        self.tiles: list[list[Tile]] = [[Tile(x, y) if (x + y) % 2 else None for y in range(Tile.Count)] for x in range(Tile.Count)]

        self.players: list[Player] = []

        self.victor: Optional[Player] = None

    def setPlayers(self, Player1: function, Player2: function, colors: list[ColorPalette]):
        self.players = [
            Player1(colors[0], False, 0),
            Player2(colors[1], True, 1)
        ]

        for x in range(Tile.Count):
            for y in range(Tile.Count - self.InitialRows, Tile.Count):
                if self.tiles[x][y]:
                    Piece(self.tiles[x][y], self.players[0])
            for y in range(self.InitialRows):
                if self.tiles[x][y]:
                    Piece(self.tiles[x][y], self.players[1])

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
        if len(self.active_player.pieces) == 0:
            self.victor = self.players[(self.players.index(self.active_player) - 1) % len(self.players)]
            if not self.no_gui:
                print("Game Over")
            return

        self.active_player.onTurnBegin(self)

    def draw(self):
        self.screen.fill(COLOR_BLACK)

        for tile in self.getTiles():
            tile.draw(self)
        for player in self.players:
            player.draw(self)

        if self.victor:
            def draw_text(x, y, color):
                surface = self.font.render("Game Over!", True, color)
                self.screen.blit(surface, ((Tile.Size * Tile.Count - surface.get_width()) / 2 + x, (Tile.Size * (Tile.Count - 1) - surface.get_height()) / 2 + y))
                surface = self.font.render(f"{self.victor.__class__.__name__} won!", True, color)
                self.screen.blit(surface, ((Tile.Size * Tile.Count - surface.get_width()) / 2 + x, (Tile.Size * (Tile.Count + 1) - surface.get_height()) / 2 + y))

            draw_text(5, 5, self.victor.color_palette.secondary)
            draw_text(0, 0, self.victor.color_palette.primary_light)

        self.draw_debug()
        pygame.display.update()

    def screenshot(self, name: str):
        pygame.image.save(self.screen, name + ".png")

    def run(self):
        if self.victor:
            return

        if not self.no_gui:
            self.clock.tick(self.Framerate)

        self.active_player.run(self)

    def click(self, pos: pygame.math.Vector2):
        for tile in self.getTiles():
            if tile.rect.collidepoint(pos):
                self.active_player.onClick(tile, self)

    def draw_debug(self):
        def print_text(y, text):
            surface = self.font_debug.render(text, False, self.players[1].color_palette.secondary)
            pygame.draw.rect(self.screen, (0, 0, 0), (0, y * self.font_debug.get_height(), surface.get_width(), surface.get_height()))
            self.screen.blit(surface, (0, y * self.font_debug.get_height()))

        print_text(0, f"Active player: {self.active_player.__class__.__name__}")
        for i in range(len(self.players)):
            print_text(i + 1, f"{self.players[i].__class__.__name__}'s score: {self.players[i].calculateScore()}")
