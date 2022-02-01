from __future__ import annotations
from typing import Generator, Optional
from collections import defaultdict
from dataclasses import dataclass
from random import choices
from os import environ
import sys
import pygame

import computer

DEBUG = int(environ.get("DEBUG", "0"))

COLOR_BLACK = pygame.Color(0x21, 0x21, 0x21)
COLOR_WHITE = pygame.Color(0xfa, 0xfa, 0xfa)


class ColorPalette:
    def __init__(self, *params):
        params = iter(params)

        def parse_color():
            if string := next(params, None):
                return pygame.Color(int(string[1:3], 16), int(string[3:5], 16), int(string[5:7], 16))
            else:
                return pygame.Color(0, 0, 0)
        self.primary = parse_color()
        self.primary_light = parse_color()
        self.primary_dark = parse_color()
        self.secondary = parse_color()
        self.secondary_light = parse_color()
        self.secondary_dark = parse_color()


COLOR_PALETTES = [
    ColorPalette("#0d47a1", "#5472d3", "#002171", "#ffc41e"),  # blue
    ColorPalette("#b71c1c", "#f05545", "#7f0000", "#00a7a6"),  # red
    ColorPalette("#1b5e20", "#4c8c4a", "#003300", "#d48dc4"),  # green
]


class vec2:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __add__(self, other: vec2) -> vec2:
        return vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: vec2) -> vec2:
        return vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: int) -> vec2:
        return vec2(self.x * other, self.y * other)

    def __floordiv__(self, other: int) -> vec2:
        return vec2(self.x // other, self.y // other)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, vec2) and self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def distance(self, other: vec2) -> float:
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def center(self, other: vec2) -> vec2 | None:
        vec = self + other
        if vec.x % 2 or vec.y % 2:
            return None
        return vec // 2

    def __str__(self):
        return f"vec2({self.x}, {self.y})"

    def __repr__(self):
        return self.__str__()


def vectorize(generator: Generator[tuple[int, int]]) -> Generator[vec2]:
    for x, y in generator:
        yield vec2(x, y)


class Tile:
    Count = 8
    Size = 100

    NO_TILE: Tile
    EMPTY: Tile

    def __init__(self, c: str):
        self._value = c
        self.piece = Piece(c) if c not in " ." else None

    def empty(self) -> bool:
        return self.piece is None and self is not Tile.NO_TILE


Tile.NO_TILE = Tile(" ")
Tile.EMPTY = Tile(".")


class Piece:
    Size = Tile.Size * 0.45

    def __init__(self, c: str):
        assert c in "12ab"
        self._value = c
        self.player = Player.ONE if c in "1a" else Player.TWO
        self.king = c in "ab"


class Player:
    ONE: Player
    TWO: Player

    Players: list[Player]

    def __init__(self, color_palette: ColorPalette, name: str):
        self.colors = color_palette
        self.name = name

    def other(self):
        return Player.Players[1 - Player.Players.index(self)]


c1, c2 = choices(COLOR_PALETTES, k=2)

Player.ONE = Player(c1, "Player")
Player.TWO = Player(c2, "Computer")
Player.Players = [Player.ONE, Player.TWO]


class Game:
    def __init__(self):
        self.board = Board()

        self.clock = pygame.time.Clock()

        self.drawer = Drawer()
        self.drawer.setup_window()
        self.refresh = True
        self.victor: Optional[Player] = None

        self.active_player = Player.ONE
        self.selected_piece: Optional[vec2] = None
        self.locked_piece: Optional[vec2] = None

        self.moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
        self.computer_data: tuple[list[tuple[vec2, vec2]], int, int, int] = ([], 0, 0, 5)
        self.generate_moves()

    def draw(self):
        if self.refresh or self.drawer.animating:
            self.refresh = False
            self.drawer.draw(self)

    def handle_click(self, click: pygame.math.Vector2):
        for pos in Board.AllTiles:
            rect = pygame.Rect(pos.x * Tile.Size, pos.y * Tile.Size, Tile.Size, Tile.Size)
            if rect.collidepoint(click):
                if (piece := self.board.get(pos).piece) and piece.player == self.active_player == Player.ONE and pos != self.selected_piece and self.get_moves(pos):
                    self.selected_piece = pos
                elif self.selected_piece and pos in self.get_moves(self.selected_piece):
                    self.move_piece(self.selected_piece, pos)
                else:
                    self.selected_piece = None
                self.refresh = True
                break

    def generate_moves(self):
        capturing_moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
        all_moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
        for tile in [self.locked_piece] if self.locked_piece else self.board.get_player_pieces(self.active_player):
            for move, capturing in self.board.get_piece_moves(tile):
                if capturing:
                    capturing_moves[tile].append(move)
                all_moves[tile].append(move)
        self.moves = capturing_moves or (defaultdict(list) if self.locked_piece else all_moves)

    def get_moves(self, pos: vec2) -> list[vec2]:
        return self.moves[pos]

    def move_piece(self, pos: vec2, pos2: vec2):
        piece = self.board.get(pos).piece
        self.board.move(pos, pos2)
        self.drawer.animate(pos, pos2)
        if not piece.king and pos2.y in (0, Tile.Count - 1):
            self.board.set(pos2, Tile("a" if piece.player == Player.ONE else "b"))
            self.next_turn()
        elif pos.distance(pos2) == 2:
            self.locked_piece = pos2
            self.generate_moves()
            self.selected_piece = pos2
            if not self.moves:
                self.next_turn()
        else:
            self.next_turn()

    def next_turn(self):
        self.active_player = self.active_player.other()
        self.selected_piece = None
        self.locked_piece = None
        self.refresh = True
        self.generate_moves()
        self.check_win()

    def check_win(self):
        if not next(self.board.get_player_pieces(self.active_player), False) or not self.moves:
            self.victor = Player.other(self.active_player)

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_presses = pygame.mouse.get_pressed()
                if mouse_presses[0] and self.active_player == Player.ONE and not self.victor:
                    self.handle_click(pygame.mouse.get_pos())
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.drawer.save_screenshot("screenshot")
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

        if self.active_player == Player.TWO and not self.victor and not self.drawer.animating:
            if not self.computer_data[0]:
                self.computer_data = computer.run(self.board, self.active_player)
            else:
                self.move_piece(*self.computer_data[0].pop(0))

        self.clock.tick(Drawer.Framerate)


class Board:
    AllTiles = list(vec2(x, y) for y in range(Tile.Count) for x in range(Tile.Count))
    Tiles = list(vec for vec in AllTiles if (vec.x + vec.y) % 2)

    def __init__(self, string: str | None = None):
        if string:
            self.grid = string
            return

        self.grid = " " * Tile.Count * Tile.Count

        for pos in Board.Tiles:
            self.set(pos, Tile("."))
            if pos.y < 3:
                self.set(pos, Tile("2"))
            elif pos.y >= Tile.Count - 3:
                self.set(pos, Tile("1"))

    def copy(self):
        return Board(self.grid)

    def score(self, player: Player) -> int:
        other = Player.other(player)

        def evaluate(pos: vec2) -> int:
            piece = self.get(pos).piece
            if not piece.king:
                return (
                    + 3
                    + (1 if pos.x == 0 or pos.x == Tile.Count - 1 else 0)
                    + (1 if pos.y == 0 or pos.y == Tile.Count - 1 else 0)
                )
            else:
                return (
                    7
                )

        return sum(map(evaluate, self.get_player_pieces(player))) - sum(map(evaluate, self.get_player_pieces(other)))

    def get(self, pos: vec2) -> Tile:
        if not Board.IsInBoard(pos) or (t := self.grid[pos.x + pos.y * Tile.Count]) == " ":
            return Tile.NO_TILE
        elif t == ".":
            return Tile.EMPTY
        return Tile(t)

    def set(self, pos: vec2, value: Tile) -> None:
        i = pos.x + pos.y * Tile.Count
        self.grid = self.grid[:i] + value._value + self.grid[i + 1:]

    def IsInBoard(pos: vec2) -> bool:
        return 0 <= pos.x < Tile.Count and 0 <= pos.y < Tile.Count

    def IsTile(pos: vec2) -> bool:
        return Board.IsInBoard(pos) and (pos.x + pos.y) % 2

    def AdjacentTiles(pos: vec2) -> Generator[vec2]:
        directions = [vec2(1, 1), vec2(1, -1), vec2(-1, 1), vec2(-1, -1)]
        for direction in directions:
            if Board.IsInBoard(res := pos + direction):
                yield res

    def get_player_pieces(self, player: Player) -> Generator[vec2]:
        for tile in Board.Tiles:
            if (piece := self.get(tile).piece) and piece.player == player:
                yield tile

    def get_piece_moves(self, pos: vec2) -> Generator[tuple[vec2, bool]]:
        if piece := self.get(pos).piece:
            for tile in Board.AdjacentTiles(pos):
                if (piece.king or ((tile.y > pos.y) == (piece.player == Player.TWO))):
                    if (target := self.get(tile)).empty():
                        yield tile, False
                    elif target.piece.player != piece.player and self.get(res := tile + (tile - pos)).empty():
                        yield res, True

    def move(self, pos: vec2, pos2: vec2) -> None:
        if (tile := self.get(pos)).piece:
            self.set(pos2, tile)
            self.set(pos, Tile.EMPTY)
            if center := pos.center(pos2):
                self.set(center, Tile.EMPTY)


@dataclass
class PieceAnimation:
    origin: Optional[vec2]
    destination: Optional[vec2]
    progress: float


class Drawer:
    FontSize = 13
    Framerate = 60
    AnimationDuration = 200

    def setup_window(self) -> None:
        pygame.init()
        pygame.font.init()

        pygame.display.set_caption("Checkers")
        self.screen = pygame.display.set_mode((Tile.Count * Tile.Size, Tile.Count * Tile.Size))
        self.font = pygame.font.SysFont("SF Pro Display", int(Tile.Size * 0.9), True)
        self.font_debug = pygame.font.SysFont("Menlo", self.FontSize)

        self.animation = PieceAnimation(None, None, 0)

    @property
    def animating(self):
        return self.animation.origin is not None

    def save_screenshot(self, name: str):
        pygame.image.save(self.screen, name + ".png")

    def draw(self, game: Game) -> None:
        self.screen.fill(COLOR_BLACK)

        for tile in Board.Tiles:
            self.draw_tile(tile)

        for player in Player.Players:
            for tile in game.board.get_player_pieces(player):
                self.draw_piece(tile, game)

        if DEBUG >= 1:
            self.draw_debug(game)

        if game.victor:
            self.draw_victory(game.victor)

        pygame.display.update()

    def draw_tile(self, pos: vec2):
        self.rect = pygame.draw.rect(self.screen, COLOR_WHITE, (pos.x * Tile.Size, pos.y * Tile.Size, Tile.Size, Tile.Size))

    def draw_victory(self, player: Player):
        def draw_text(x, y, color):
            surface = self.font.render("Game Over!", True, color)
            self.screen.blit(surface, ((Tile.Size * Tile.Count - surface.get_width()) / 2 + x, (Tile.Size * (Tile.Count - 1) - surface.get_height()) / 2 + y))
            surface = self.font.render(f"{player.name} wins!", True, color)
            self.screen.blit(surface, ((Tile.Size * Tile.Count - surface.get_width()) / 2 + x, (Tile.Size * (Tile.Count + 1) - surface.get_height()) / 2 + y))

        draw_text(5, 5, player.colors.secondary)
        draw_text(0, 0, player.colors.primary_light)

    def animate(self, pos: vec2, pos2: vec2):
        self.animation = PieceAnimation(pos, pos2, 0)

    def draw_piece(self, pos: vec2, game: Game):
        position = pos
        if self.animation.destination == pos:
            position = self.animation.origin * (1 - self.animation.progress) + self.animation.destination * self.animation.progress
            if self.animation.progress >= 1:
                self.animation = PieceAnimation(None, None, 0)
            self.animation.progress = min(self.animation.progress + 1000 / self.Framerate / self.AnimationDuration, 1)

        piece = game.board.get(pos).piece
        colors = piece.player.colors
        active = game.active_player == piece.player == Player.ONE
        selected = game.selected_piece == pos and piece.player == Player.ONE
        moves = list(game.get_moves(pos))

        def draw_piece(x, y, color, radius=Piece.Size):
            if piece.king:
                z = Tile.Size // 20
                a = z * 4
                b = z * 5
                c = Tile.Size - b
                d = b - a
                e = Tile.Size - 2 * d
                f = Tile.Size - 2 * b

                pygame.draw.circle(self.screen, color, (x * Tile.Size + b, y * Tile.Size + b), a)
                pygame.draw.circle(self.screen, color, (x * Tile.Size + c, y * Tile.Size + b), a)
                pygame.draw.circle(self.screen, color, (x * Tile.Size + c, y * Tile.Size + c), a)
                pygame.draw.circle(self.screen, color, (x * Tile.Size + b, y * Tile.Size + c), a)
                pygame.draw.rect(self.screen, color, (x * Tile.Size + b, y * Tile.Size + d, f, e))
                pygame.draw.rect(self.screen, color, (x * Tile.Size + d, y * Tile.Size + b, e, f))
            else:
                pygame.draw.circle(self.screen, color, ((x + 0.5) * Tile.Size, (y + 0.5) * Tile.Size), radius)

        def draw_shadow():
            draw_piece(position.x - 0.01, position.y - 0.01, COLOR_BLACK)

        if not active or not moves:
            draw_piece(position.x, position.y, colors.primary_dark)

        elif selected:
            draw_shadow()
            draw_piece(position.x + 0.1, position.y + 0.1, colors.primary_light)

        else:
            draw_piece(position.x, position.y, colors.primary)

        if selected and moves:
            for move in moves:
                draw_piece(move.x, move.y, colors.secondary)

    def draw_debug(self, game: Game):
        for tile in Board.Tiles:
            surface = self.font_debug.render(f"{tile.x},{tile.y}", True, COLOR_BLACK)
            self.screen.blit(surface, (tile.x * Tile.Size, tile.y * Tile.Size))

        surfaces: list[pygame.Surface] = []

        def print_text(y, text):
            surfaces.append(self.font_debug.render(text, False, COLOR_WHITE))
            pygame.draw.rect(self.screen, (0, 0, 0), (0, y * self.font_debug.get_height(), surface.get_width(), surface.get_height()))
            self.screen.blit(surface, (0, y * self.font_debug.get_height()))

        print_text(0, f"Active player: {game.active_player.name}")
        print_text(1, f"Selected piece: {game.selected_piece}")
        print_text(2, f"Computer score: {game.computer_data[1]}")
        print_text(2, f"Elapsed time: {game.computer_data[2]} / 2000")
        print_text(2, f"Minimax depth: {game.computer_data[3]} / 7")

        width = max(map(pygame.Surface.get_width, surfaces))
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, width, len(surfaces) * self.font_debug.get_height()))
        for y, surface in enumerate(surfaces):
            self.screen.blit(surface, (0, y * self.font_debug.get_height()))
