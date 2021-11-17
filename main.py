from __future__ import annotations
import pygame
import sys
import random

from checkers import *
from testificates import *


COLOR_PALETTES = [
    ColorPalette("#0d47a1", "#5472d3", "#002171", "#ffc41e", "#ffd149", "#c67100"),  # blue
    ColorPalette("#b71c1c", "#f05545", "#7f0000", "#00a7a6", "#ff7961", "#ba000d"),  # red
    ColorPalette("#1b5e20", "#4c8c4a", "#003300", "#d48dc4", "#ffd149", "#c67100"),  # green
]


class HumanPlayer(Player):
    def __init__(self, color: ColorPalette, direction: bool):
        super().__init__(color, direction)
        self.selected_piece: Piece = None

    def select_piece(self, piece: Piece):
        if self.selected_piece is not None:
            self.selected_piece.is_selected = False
        self.selected_piece = piece
        if self.selected_piece is not None:
            piece.is_selected = True

    def onClick(self, tile: Tile, game: Game):
        if tile.piece:
            if tile.piece.player is self:
                if tile.piece is not self.selected_piece:
                    self.select_piece(tile.piece)
                else:
                    self.select_piece(None)
        elif self.selected_piece:
            for move in self.moves[self.selected_piece]:
                if move.target_tile is tile:
                    if self.selected_piece.moveTo(move, game):
                        self.locked_piece = self.selected_piece
                        self.moves = self.get_possible_moves(game)
                    else:
                        game.nextTurn()
                    break

    def draw(self, screen: pygame.Surface):
        for piece in self.pieces:
            piece.draw(screen, self.moves[piece] if self.moves else None)

    def onTurnEnd(self, game: Game):
        super().onTurnEnd(game)

        self.select_piece(None)


game = Game()

game.setPlayers(HumanPlayer, Chuck, random.sample(COLOR_PALETTES, 2))


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
                pygame.image.save(game.screen, "screenshot.png")
            elif event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

    game.run()
