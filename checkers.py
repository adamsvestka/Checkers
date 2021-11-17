from __future__ import annotations
import pygame
import sys
import random


TILE_COUNT = 8
TILE_SIZE = 100


COLOR_BLACK = pygame.Color(0x21, 0x21, 0x21)
COLOR_WHITE = pygame.Color(0xfa, 0xfa, 0xfa)


pygame.init()
pygame.display.set_caption("Checkers")
FPS = pygame.time.Clock()
screen = pygame.display.set_mode((TILE_COUNT * TILE_SIZE, TILE_COUNT * TILE_SIZE))


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


COLOR_PALETTES = [
    ColorPalette("#0d47a1", "#5472d3", "#002171", "#ffc41e", "#ffd149", "#c67100"),  # blue
    ColorPalette("#b71c1c", "#f05545", "#7f0000", "#00a7a6", "#ff7961", "#ba000d"),  # red
    ColorPalette("#1b5e20", "#4c8c4a", "#003300", "#d48dc4", "#ffd149", "#c67100"),  # green
]


class Tile:
    size = TILE_SIZE

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.piece: Piece = None

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Tile):
            return self.x == o.x and self.y == o.y
        return False

    def draw(self):
        self.rect = pygame.draw.rect(screen, COLOR_WHITE, (self.x * Tile.size, self.y * Tile.size, Tile.size, Tile.size))


class Move:
    def __init__(self, tile: Tile, target: Piece = None):
        self.tile = tile
        if target is not None:
            self.target: Piece = target
            self.capture = True
        else:
            self.target = None
            self.capture = False


class Piece:
    size = TILE_SIZE * 0.45

    def __init__(self, tile: Tile, player: Player):
        self.tile: Tile = tile
        self.active = False
        self.tile.piece = self
        self.player = player
        self.tier = False

    def __hash__(self):
        return hash((self.tile.x, self.tile.y))

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Piece):
            return self.tile == o.tile
        return False

    def moveTo(self, move: Move):
        """
        Execute a move, automatically capturing if necessary.

        Returns True if further captures are possible, otherwise False.
        """
        self.tile.piece = None
        self.tile = move.tile
        self.tile.piece = self

        if self.tile.y == (TILE_COUNT - 1 if self.player.direction else 0):
            self.tier = True
            if move.capture:
                move.target.capture()
            return False

        if move.capture:
            move.target.capture()
            for move in self.getPossibleMoves():
                if move.capture:
                    return True

        return False

    def getPossibleMoves(self):
        if self.player.locked_piece is not None and self.player.locked_piece is not self:
            return

        x, y = self.tile.x, self.tile.y
        dir = 1 if self.player.direction else -1

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

        if self.tier:
            tile = get_diagonal_tile(1, -dir)
            if tile:
                yield tile
            tile = get_diagonal_tile(-1, -dir)
            if tile:
                yield tile

    def capture(self):
        self.player.pieces.remove(self)
        self.tile.piece = None

    def draw(self, moves: list[Move] = None):
        def draw_piece(x, y, color, radius=self.size):
            if self.tier:
                z = Tile.size // 20
                a = z * 4
                b = z * 5
                c = Tile.size - b
                d = b - a
                e = Tile.size - 2 * d
                f = Tile.size - 2 * b

                pygame.draw.circle(screen, color, (x * Tile.size + b, y * Tile.size + b), a)
                pygame.draw.circle(screen, color, (x * Tile.size + c, y * Tile.size + b), a)
                pygame.draw.circle(screen, color, (x * Tile.size + c, y * Tile.size + c), a)
                pygame.draw.circle(screen, color, (x * Tile.size + b, y * Tile.size + c), a)
                pygame.draw.rect(screen, color, (x * Tile.size + b, y * Tile.size + d, f, e))
                pygame.draw.rect(screen, color, (x * Tile.size + d, y * Tile.size + b, e, f))
            else:
                pygame.draw.circle(screen, color, ((x + 0.5) * Tile.size, (y + 0.5) * Tile.size), radius)

        def draw_shadow():
            draw_piece(self.tile.x - 0.01, self.tile.y - 0.01, COLOR_BLACK)

        if not self.player.active or not moves:
            draw_piece(self.tile.x, self.tile.y, self.player.color.primary_dark)

        elif self.active:
            draw_shadow()
            draw_piece(self.tile.x + 0.1, self.tile.y + 0.1, self.player.color.primary_light, self.size + 1)
            if moves:
                for move in moves:
                    draw_piece(move.tile.x, move.tile.y, self.player.color.secondary)
                    # pygame.draw.rect(screen, self.player.color.secondary, (move.tile.x * Tile.size, move.tile.y * Tile.size, Tile.size, Tile.size))

        else:
            draw_piece(self.tile.x, self.tile.y, self.player.color.primary)


class Player:
    def __init__(self, color: ColorPalette, direction: bool):
        self.color = color
        self.pieces: list[Piece] = []
        self.direction = direction
        self.active = False
        self.moves: dict[Piece, list[Move]] = None
        self.locked_piece: Piece = None

    def get_possible_moves(self):
        moves: dict[Piece, list[Move]] = {}
        capturing = False
        for piece in self.pieces:
            moves[piece] = []
            for move in piece.getPossibleMoves():
                if not capturing and move.capture:
                    capturing = True
                    for piece in moves:
                        moves[piece] = [move for move in moves[piece] if move.capture]

                if not capturing or move.capture:
                    moves[piece].append(move)

        return moves

    def onClick(self, tile: Tile):
        pass

    def draw(self):
        for piece in self.pieces:
            piece.draw()

    def onTurnBegin(self):
        self.active = True
        self.moves = self.get_possible_moves()

    def onTurnEnd(self):
        self.active = False
        self.moves = None
        self.locked_piece = None


class HumanPlayer(Player):
    def __init__(self, color: ColorPalette, direction: bool):
        super().__init__(color, direction)
        self.selected_piece: Piece = None

    def select_piece(self, piece: Piece):
        if self.selected_piece is not None:
            self.selected_piece.active = False
        self.selected_piece = piece
        if self.selected_piece is not None:
            piece.active = True

    def onClick(self, tile: Tile):
        if tile.piece:
            if tile.piece.player is self:
                if tile.piece is not self.selected_piece:
                    self.select_piece(tile.piece)
                else:
                    self.select_piece(None)
        elif self.selected_piece:
            for move in self.moves[self.selected_piece]:
                if move.tile is tile:
                    if self.selected_piece.moveTo(move):
                        self.locked_piece = self.selected_piece
                        self.moves = self.get_possible_moves()
                    else:
                        game.nextTurn()
                    break

    def draw(self):
        for piece in self.pieces:
            piece.draw(self.moves[piece])

    def onTurnEnd(self):
        super().onTurnEnd()

        self.select_piece(None)


class Game:
    def __init__(self):
        self.tiles: list[list[Tile]] = [[Tile(x, y) if (x + y) % 2 else None for y in range(TILE_COUNT)] for x in range(TILE_COUNT)]

        self.players: list[Player] = []

        colors = random.sample(COLOR_PALETTES, 2)
        self.players.append(HumanPlayer(colors[0], False))
        self.players.append(Chuck(colors[1], True))
        for x in range(TILE_COUNT):
            for y in range(TILE_COUNT - 3, TILE_COUNT):
                if self.tiles[x][y]:
                    self.players[0].pieces.append(Piece(self.tiles[x][y], self.players[0]))
            for y in range(3):
                if self.tiles[x][y]:
                    self.players[1].pieces.append(Piece(self.tiles[x][y], self.players[1]))

        self.activePlayer = self.players[-1]

    def getTiles(self):
        return (tile for row in self.tiles for tile in row if tile)

    def getTileAt(self, x, y):
        if x < 0 or x >= TILE_COUNT or y < 0 or y >= TILE_COUNT:
            return None
        return self.tiles[x][y]

    def nextTurn(self):
        self.activePlayer.onTurnEnd()

        self.activePlayer = self.players[(self.players.index(self.activePlayer) + 1) % len(self.players)]

        self.activePlayer.onTurnBegin()

    def draw(self):
        screen.fill(COLOR_BLACK)
        for tile in self.getTiles():
            tile.draw()
        for player in self.players:
            player.draw()
        pygame.display.update()

    def click(self, pos: pygame.math.Vector2):
        for tile in self.getTiles():
            if tile.rect.collidepoint(pos):
                self.activePlayer.onClick(tile)


class Chuck(Player):
    def onTurnBegin(self):
        super().onTurnBegin()

        if len(self.moves) == 0:
            print("No moves")

        else:
            while True:
                piece = random.choice(list(self.moves.keys()))
                if len(self.moves[piece]) > 0:
                    piecemoves = self.moves[piece]
                    move = random.choice(piecemoves)
                    while piece.moveTo(move):
                        piecemoves = list(piece.getPossibleMoves())
                        move = random.choice(piecemoves)
                    break

        game.nextTurn()


game = Game()

game.nextTurn()


while True:
    game.draw()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_presses = pygame.mouse.get_pressed()
            if mouse_presses[0]:
                game.click(pygame.mouse.get_pos())
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                pygame.image.save(screen, "screenshot.png")
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

    FPS.tick(60)
