from __future__ import annotations
from typing import Iterator, Optional
from env import DEBUG, TARGET_TIME, MINIMUM_DEPTH
from collections import defaultdict
from dataclasses import dataclass
from random import sample
import sys
import pygame

import computer


COLOR_BLACK = pygame.Color(0x21, 0x21, 0x21)
COLOR_WHITE = pygame.Color(0xfa, 0xfa, 0xfa)


class ColorPalette:
    """Used for coloring a player's pieces.

    Primary light and dark should be a lighter/darker version of the primary color. Secondary should be a contrasting color to primary.

    May be initialized with an arbitrary amount of colors (up to 6).

    Parameters
    ----------
    *params : ``str``, default ``#000000``
        Hex strings in the format of ``#RRGGBB``.

    Attributes
    ----------
    primary : ``pygame.Color``
        Color of pieces which can move.
    primary_light : ``pygame.Color``
        Color of the currently selected piece.
    primary_dark : ``pygame.Color``
        Color of pieces which cannot move.
    secondary : ``pygame.Color``
        Color of possible move indicators.
    secondary_light : ``pygame.Color``
        Unused.
    secondary_dark : ``pygame.Color``
        Unused.

    Notes
    -----
    Secondary light and dark variants are currently unused and don't have to be set.
    """

    def __init__(self, *params: str):
        params = iter(params)

        def parse_color() -> pygame.Color:
            """Helper function to retrieve colors from method input."""
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
    """A 2D vector used for to represent a position on the board.

    Parameters
    ----------
    x : ``int``
        The x-coordinate of the vector.
    y : ``int``
        The y-coordinate of the vector.

    Attributes
    ----------
    x : ``int``
        The x-coordinate of the vector.
    y : ``int``
        The y-coordinate of the vector.
    """

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

    def distance(self, other: vec2) -> int:
        """Return the Manhattan distance between two vectors.

        Parameters
        ----------
        other : :class:`vec2`
            The other vector.

        Returns
        -------
        ``int``
            The distance between the two vectors.
        """
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def center(self, other: vec2) -> Optional[vec2]:
        """Return the center of two vectors.

        Parameters
        ----------
        other : :class:`vec2`
            The other vector.

        Returns
        -------
        ``Optional[vec2]``
            The center of the two vectors, or None if the center doesn't fall on an integer grid.
        """
        vec = self + other
        if vec.x % 2 or vec.y % 2:
            return None
        return vec // 2

    def __str__(self):
        return f"vec2({self.x}, {self.y})"

    def __repr__(self):
        return self.__str__()


def vectorize(generator: Iterator[tuple[int, int]]) -> Iterator[vec2]:
    """Convert a generator of tuples to a generator of vectors.

    Parameters
    ----------
    generator : ``Iterator[tuple[int, int]]``
        The generator to convert.

    Yields
    -------
    :class:`vec2`
        The converted generator.
    """
    for x, y in generator:
        yield vec2(x, y)


class Tile:
    """A tile on the board, doesn't have to be a valid position, may have a piece on it.

    Should be treated as **immutable**. Initialize a Tile from its character representation.

    Possible characters are:
        - ``[space]``: No tile
        - ``.``: Empty tile
        - ``1``: Player 1's piece
        - ``2``: Player 2's piece
        - ``a``: Player 1's king piece
        - ``b``: Player 2's king piece

    Parameters
    ----------
    c : ``str``
        The character representation of the tile.

    Raises
    ------
    AssertionError
        If the character representation is invalid.

    Attributes
    ----------
    piece : ``Optional[Piece]``
        The piece on the tile, or None if there is no piece.

    See Also
    --------
    :class:`Piece`
    """
    Count: int = 8
    """Board width and height in tiles."""
    Size: int = 100
    """Tile size in pixels."""

    NO_TILE: Tile
    """Static instance of invalid tile position."""
    EMPTY: Tile
    """Static instance of empty tile."""

    def __init__(self, c: str):
        assert c in " .12ab"
        self._value = c
        self.piece = Piece(c) if c not in " ." else None

    def empty(self) -> bool:
        """Return whether the tile doesn't have a piece on it. If the tile isn't valid returns True."""
        return self.piece is None and self is not Tile.NO_TILE


Tile.NO_TILE = Tile(" ")
Tile.EMPTY = Tile(".")


class Piece:
    """A piece on the board, movable by it's owner.

    Should be treated as **immutable**. Initialize a Piece from its character representation.

    Possible characters are:
        - ``1``: Player 1's piece
        - ``2``: Player 2's piece
        - ``a``: Player 1's king piece
        - ``b``: Player 2's king piece

    Parameters
    ----------
    c : ``str``
        The character representation of the piece.

    Raises
    ------
    AssertionError
        If the character representation is invalid.

    Attributes
    ----------
    player : :class:`Player`
        The player who owns the piece.
    king : ``bool``
        Whether the piece is a king or a normal piece.

    See Also
    --------
    :class:`Tile`
    :class:`Player`
    """
    Size: int = int(Tile.Size * 0.45)

    def __init__(self, c: str):
        assert c in "12ab"
        self._value = c
        self.player = Player.ONE if c in "1a" else Player.TWO
        self.king = c in "ab"


class Player:
    """One of the two players in the game.

    Should be treated as **immutable**. There is a static instance for each player, which acts as a enumeration.
    Each instance holds a color palette for its pieces.

    Parameters
    ----------
    color_palette : :class:`ColorPalette`
        The color palette of the player.
    name : ``str``
        The name of the player.

    Attributes
    ----------
    colors : :class:`ColorPalette`
        Defines the drawing color of the player's pieces.
    name : ``str``
        Used to congratulate the player in the victory screen.

    See Also
    --------
    :class:`Piece`
    """
    ONE: Player
    """Static instance of the first player, the human player."""
    TWO: Player
    """Static instance of the second player, the computer player."""

    Players: list[Player]
    """Static list of all players."""

    def __init__(self, color_palette: ColorPalette, name: str):
        self.colors = color_palette
        self.name = name

    def other(self) -> Player:
        """Returns a reference to the other player."""
        return Player.Players[1 - Player.Players.index(self)]


# Two random color palettes are selected
c1, c2 = sample(COLOR_PALETTES, 2)

Player.ONE = Player(c1, "Player")
Player.TWO = Player(c2, "Computer")
Player.Players = [Player.ONE, Player.TWO]


class Board:
    """Manages the game board state.

    Create a new board with the default configuration or from a string.

    Default board configuration:

    .. code-block:: python3

        grid: str = (
            " 2 2 2 2"
            "2 2 2 2 "
            " 2 2 2 2"
            ". . . . "
            " . . . ."
            "1 1 1 1 "
            " 1 1 1 1"
            "1 1 1 1 "
        )

    Parameters
    ----------
    string : ``str``, optional
        The string representation of the board. A string of length ``Tile.Count * Tile.Count`` and containing only ``" .12ab"``.

    Attributes
    ----------
    grid : ``str``
        A string representation of the board.
    """
    AllTiles: list[vec2] = list(vec2(x, y) for y in range(Tile.Count) for x in range(Tile.Count))
    """Static list of all positions inside the board."""
    Tiles: list[vec2] = list(vec for vec in AllTiles if (vec.x + vec.y) % 2)
    """Static list of all *valid* tiles on the board, used for fast iteration over all tiles."""

    def __init__(self, string: Optional[str] = None):
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

    def copy(self) -> Board:
        """Clone the board, used for the AI's branching algorithm."""
        return Board(self.grid)

    def score(self, player: Player) -> int:
        """Evaluate the board configuration in favor of the given player.

        This is the scoring function used by the AI. The oponent's score is subtracted from the player's score.

        Scoring principles:

            - Score is proportional to the number of the player's pieces.
            - King pieces are worth more than normal pieces.
            - Normal pieces get a bonus if they stick to the edges of the board.

        Parameters
        ----------
        player : :class:`Player`
            The player to evaluate the board for.

        Returns
        -------
        ``int``
            The score of the player.
        """
        other = player.other()

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
        """Return information about the tile at the given position.

        Parameters
        ----------
        pos : :class:`vec2`
            The queried position.

        Returns
        -------
        :class:`Tile`
            The tile at the given position or :attr:`Tile.NO_TILE` if the position is invalid.
        """
        if not Board.IsInBoard(pos) or (t := self.grid[pos.x + pos.y * Tile.Count]) == " ":
            return Tile.NO_TILE
        elif t == ".":
            return Tile.EMPTY
        return Tile(t)

    def set(self, pos: vec2, value: Tile) -> None:
        """Set the tile at the given position.

        Parameters
        ----------
        pos : :class:`vec2`
            The position to set the tile at.
        value : :class:`Tile`
            The value to set the tile to.

        Notes
        -----
            - This method does not check if the position is valid.
            - This method only uses the :attr:`Tile._value` property, so any object that implements it can be used.
        """
        i = pos.x + pos.y * Tile.Count
        self.grid = self.grid[:i] + value._value + self.grid[i + 1:]

    def IsInBoard(pos: vec2) -> bool:
        """Check if the given position is inside the board."""
        return 0 <= pos.x < Tile.Count and 0 <= pos.y < Tile.Count

    def IsTile(pos: vec2) -> bool:
        """Check if the given position is a valid tile."""
        return Board.IsInBoard(pos) and (pos.x + pos.y) % 2

    def AdjacentTiles(pos: vec2) -> Iterator[vec2]:
        """Return an iterator of all adjacent tiles to the given position.

        Does not check if the position is a valid tile, it will return diagonally adjacent tiles either way.
        However, it will not return tiles that are not within the board.

        Parameters
        ----------
        pos : :class:`vec2`
            The position to get the adjacent tiles for.

        Yields
        -------
        :class:`vec2`
            The adjacent tile.
        """
        directions = [vec2(1, 1), vec2(1, -1), vec2(-1, 1), vec2(-1, -1)]
        for direction in directions:
            if Board.IsInBoard(res := pos + direction):
                yield res

    def get_player_pieces(self, player: Player) -> Iterator[vec2]:
        """Return an iterator of all pieces belonging to the given player.

        Loops over all tiles and yields positions of tiles belonging to the given player.

        Parameters
        ----------
        player : :class:`Player`
            The player to get the pieces for.

        Yields
        -------
        :class:`vec2`
            The position of the piece.
        """
        for tile in Board.Tiles:
            if (piece := self.get(tile).piece) and piece.player == player:
                yield tile

    def get_piece_moves(self, pos: vec2) -> Iterator[tuple[vec2, bool]]:
        """Return an iterator of all possible moves for the piece at the given position.

        A piece can move one tile diagonally in its player's direction. If the piece is a king, it can move in any direction.
        If there is an enemy piece on the tile and the space behind it is empty, the piece *jump over* the enemy piece and capture it.
        Capturing a piece means the piece is removed from the board.

        Parameters
        ----------
        pos : :class:`vec2`
            The position of the piece to get the moves for.

        Yields
        -------
        :class:`vec2`
            The target position of the move.
        ``bool``
            Whether the move is a capture.

        Notes
        -----
        If a player has at least one capturing move available, they have to make a capturing move. This method doesn't handle that, see :meth:`Game.generate_moves`.
        """
        if piece := self.get(pos).piece:
            for tile in Board.AdjacentTiles(pos):
                if (piece.king or ((tile.y > pos.y) == (piece.player == Player.TWO))):
                    if (target := self.get(tile)).empty():
                        yield tile, False
                    elif target.piece.player != piece.player and self.get(res := tile + (tile - pos)).empty():
                        yield res, True

    def move(self, pos: vec2, pos2: vec2) -> None:
        """Move a piece, capturing an enemy piece if applicable.

        This method does not validate the move. If there is a tile between the two positions, the piece at that tile will be captured.

        Parameters
        ----------
        pos : :class:`vec2`
            The position of the piece to move.
        pos2 : :class:`vec2`
            The target position of the move.
        """
        if (tile := self.get(pos)).piece:
            self.set(pos2, tile)
            self.set(pos, Tile.EMPTY)
            if center := pos.center(pos2):
                self.set(center, Tile.EMPTY)


class Game:
    """Takes care of game logic and user input.

    For example, makes sure players make capturing moves if they have any available, handles piece movement,
    checks for victory clauses, handles user piece selection and movement, etc.

    Attributes
    ----------
    board : :class:`Board`
        Stores the board layout.
    clock : ``pygame.time.Clock``
        Used to control the framerate.
    drawer : :class:`Drawer`
        Rendering abstraction class.
    refresh : ``bool``
        Whether the game should be redrawn, is used to limit redrawing if nothing changed.
    victor : ``Optional[Player]``
        The player that won the game, once the game is over or None if the game is still ongoing.
    active_player : :class:`Player`
        The player whose turn it is.
    selected_piece : ``Optional[vec2]``
        The position of the piece that is currently selected (only applies to human players).
    locked_piece : ``Optional[vec2]``
        If a *multi-jump* is in progress, this is the position of the piece that is currently locked.
    moves : ``defaultdict[vec2, list[vec2]]``
        A dictionary of all possible moves from each piece's position.
    computer_data : :class:`~computer.ComputerData`
        Results of the last AI computation.
    """

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
        self.computer_data: computer.ComputerData = computer.ComputerData([], 0, TARGET_TIME, MINIMUM_DEPTH)
        self.generate_moves()

    def draw(self) -> None:
        """Render the game if :attr:`refresh` is ``True`` or an animation is running :attr:`Drawer.animating`."""
        if self.refresh or self.drawer.animating:
            self.refresh = False
            self.drawer.draw(self)

    def handle_click(self, click: pygame.math.Vector2) -> None:
        """Handle a click by a human player.

        Finds the tile that was clicked and does the following:

            - If a piece is already selected and the tile is a valid move, move the piece.
            - If the tile contains a piece the player can move, select it.
            - Otherwise deselect the currently selected piece.

        Parameters
        ----------
        click : ``pygame.math.Vector2``
            The position of the click.
        """
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

    def generate_moves(self) -> None:
        """Generate all possible moves for the current player.

        Loops over all pieces belonging to the current player and generates all possible moves for each piece.
        If at least one of the moves is a capturing move, only capturing moves are kept.

        Notes
        -----
        This method is called whenever a piece is moved or it becomes the other player's turn.
        The result isn't returned, but stored in :attr:`moves`.
        """
        capturing_moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
        all_moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
        for tile in [self.locked_piece] if self.locked_piece else self.board.get_player_pieces(self.active_player):
            for move, capturing in self.board.get_piece_moves(tile):
                if capturing:
                    capturing_moves[tile].append(move)
                all_moves[tile].append(move)
        self.moves = capturing_moves or (defaultdict(list) if self.locked_piece else all_moves)

    def get_moves(self, pos: vec2) -> list[vec2]:
        """Get all possible moves for a piece, this does not generate new moves, it merely returns cached moves for the piece."""
        return self.moves[pos]

    def move_piece(self, pos: vec2, pos2: vec2) -> None:
        """Move a piece, with game logic.

        On top of calling :meth:`Board.move` does the following:

            - Begins an animation of the move.
            - If the piece reaches the other side and is not a king, it becomes a king and the turn ends immediately.
            - Otherwise if a capturing move is made, the piece is locked.
            - New moves are generated.
            - If the player cannot make any more captures with this piece, the turn ends.

        Parameters
        ----------
        pos : :class:`vec2`
            The position of the piece to move.
        pos2 : :class:`vec2`
            The target position of the move.

        See Also
        --------
        :meth:`Board.move`
        :meth:`Drawer.animate`
        :meth:`generate_moves`
        :meth:`next_turn`
        """
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

    def next_turn(self) -> None:
        """End the current player's turn and begin the next player's turn.

        Resets the locked piece and selected piece. Checks if the game is over.

        See Also
        --------
        :meth:`check_win`
        """
        self.active_player = self.active_player.other()
        self.selected_piece = None
        self.locked_piece = None
        self.refresh = True
        self.generate_moves()
        self.check_win()

    def check_win(self) -> None:
        """Check if the game is over.

        If the current player doesn't have any pieces left or all their pieces are unable to move, the player loses.
        """
        if not next(self.board.get_player_pieces(self.active_player), False) or not self.moves:
            self.victor = self.active_player.other()

    def update(self) -> None:
        """Processes user and computer input.

        Does nothing if the game is over.
        If the current player is the user, forwards mouse clicks to :meth:`handle_click`.
        If it's the computer's turn, queries the computer for a move.

        There are some available keyboard shortcuts:

            - ``q``: Quit the game.
            - ``space``: Save a screenshot of the game as ``screenshot.png``.

        This function also handles sleeping in accordance to :attr:`Drawer.Framerate`, as to not overload the CPU.

        See Also
        --------
        :meth:`draw`
        """
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
            if not self.computer_data.compound_move:
                self.computer_data = computer.run(self.board, self.active_player)
            else:
                self.move_piece(*self.computer_data.compound_move.pop(0))

        self.clock.tick(Drawer.Framerate)


@dataclass
class PieceAnimation:
    """Holds state about the currently animated piece."""
    origin: Optional[vec2]
    """The position of the piece before the animation."""
    destination: Optional[vec2]
    """The position of the piece after the animation."""
    progress: float
    """A value from 0 to 1, representing the progress of the animation."""


class Drawer:
    """Handles rendering of the game.

    Uses `pygame <https://pygame.org/>`_ for cross-platform rendering.

    Attributes
    ----------
    screen : ``pygame.Surface``
        A surface representing the game window.
    font : ``pygame.font.Font``
        The default font used for rendering text.
    font_debug : ``pygame.font.Font``
        A smaller mono-spaced font used for debugging.
    animation : :class:`PieceAnimation`
        The current animation being played.
    """
    FontSize: int = 13
    """The default font size."""
    Framerate: int = 60
    """The maximum refresh rate of the game."""
    AnimationDuration: int = 200
    """The duration of animations in milliseconds."""

    def setup_window(self) -> None:
        """Creates the game window and loads fonts."""
        pygame.init()
        pygame.font.init()

        pygame.display.set_caption("Checkers")
        self.screen = pygame.display.set_mode((Tile.Count * Tile.Size, Tile.Count * Tile.Size))
        self.font = pygame.font.SysFont("SF Pro Display", int(Tile.Size * 0.9), True)
        self.font_debug = pygame.font.SysFont("Menlo", self.FontSize)

        self.animation = PieceAnimation(None, None, 0)

    @property
    def animating(self) -> bool:
        """Whether or not an animation is currently playing."""
        return self.animation.origin is not None

    def save_screenshot(self, name: str) -> None:
        """Saves a screenshot of the game as ``<name>.png``."""
        pygame.image.save(self.screen, name + ".png")

    def draw(self, game: Game) -> None:
        """Draws the game to the screen.

        1. Clears the screen and draws the board.
        2. Draws the pieces.
        3. If :data:`env.DEBUG` is set draws extra debugging information.
        4. If the game is over, draws the victory message.

        Parameters
        ----------
        game : :class:`Game`
            The game object to draw information from.

        See Also
        --------
        :meth:`draw_tile`
        :meth:`draw_piece`
        :meth:`draw_debug`
        :meth:`draw_victory`
        """
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

    def draw_tile(self, pos: vec2) -> None:
        """Draws a board tile to the screen.

        A tile is represented as a white square.

        Parameters
        ----------
        pos : :class:`vec2`
            The position of the tile to draw.
        """
        self.rect = pygame.draw.rect(self.screen, COLOR_WHITE, (pos.x * Tile.Size, pos.y * Tile.Size, Tile.Size, Tile.Size))

    def draw_victory(self, player: Player) -> None:
        """Draws the victory message to the screen.

        Prints "Game Over! <player> wins!" in large letters to the center of the screen.

        Parameters
        ----------
        player : :class:`Player`
            The player who won the game, used to determine the color of the text and congratulations message.
        """
        def draw_text(x, y, color):
            surface = self.font.render("Game Over!", True, color)
            self.screen.blit(surface, ((Tile.Size * Tile.Count - surface.get_width()) / 2 + x, (Tile.Size * (Tile.Count - 1) - surface.get_height()) / 2 + y))
            surface = self.font.render(f"{player.name} wins!", True, color)
            self.screen.blit(surface, ((Tile.Size * Tile.Count - surface.get_width()) / 2 + x, (Tile.Size * (Tile.Count + 1) - surface.get_height()) / 2 + y))

        draw_text(5, 5, player.colors.secondary)
        draw_text(0, 0, player.colors.primary_light)

    def animate(self, pos: vec2, pos2: vec2) -> None:
        """Sets up an animation to move a piece from one position to another."""
        self.animation = PieceAnimation(pos, pos2, 0)

    def draw_piece(self, pos: vec2, game: Game) -> None:
        """Draws a piece to the screen.

        Handles animations and different piece states and types.

        * If the piece is being animated, interpolates between the origin and destination positions in regards to the animations progress.
        * If the piece cannot currently be moved it is drawn in a darker color.
        * If the piece is currently selected, it is drawn offset, in a lighter color, with a shadow under it and its possible moves are drawn in a contrasting color.
        * Otherwise if a piece can be moved but is not currently selected, it is drawn using the default color.

        A normal piece is drawn as a circle, while a king piece is drawn as a square with rounded corners.

        Parameters
        ----------
        pos : :class:`vec2`
            The position of the piece to draw.
        game : :class:`Game`
            The game object to draw information from.

        See Also
        --------
        :class:`ColorPalette`
        :attr:`Player.colors`
        """
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

        def draw_piece_(x, y, color, radius=Piece.Size):
            """Draws a shape based on the piece type."""
            if piece.king:
                z = Tile.Size // 20
                a = z * 4
                b = z * 5
                c = Tile.Size - b
                d = b - a
                e = Tile.Size - 2 * d
                f = Tile.Size - 2 * b

                # draw a squircle
                pygame.draw.circle(self.screen, color, (x * Tile.Size + b, y * Tile.Size + b), a)
                pygame.draw.circle(self.screen, color, (x * Tile.Size + c, y * Tile.Size + b), a)
                pygame.draw.circle(self.screen, color, (x * Tile.Size + c, y * Tile.Size + c), a)
                pygame.draw.circle(self.screen, color, (x * Tile.Size + b, y * Tile.Size + c), a)
                pygame.draw.rect(self.screen, color, (x * Tile.Size + b, y * Tile.Size + d, f, e))
                pygame.draw.rect(self.screen, color, (x * Tile.Size + d, y * Tile.Size + b, e, f))
            else:
                pygame.draw.circle(self.screen, color, ((x + 0.5) * Tile.Size, (y + 0.5) * Tile.Size), radius)

        def draw_shadow():
            """Draws a slightly offset dark gray shadow under the piece."""
            draw_piece_(position.x - 0.01, position.y - 0.01, COLOR_BLACK)

        if not active or not moves:
            draw_piece_(position.x, position.y, colors.primary_dark)

        elif selected:
            draw_shadow()
            draw_piece_(position.x + 0.1, position.y + 0.1, colors.primary_light)

        else:
            draw_piece_(position.x, position.y, colors.primary)

        if selected and moves:
            for move in moves:
                draw_piece_(move.x, move.y, colors.secondary)

    def draw_debug(self, game: Game) -> None:
        """Draws extra debug information to the screen.

        Labels each tile with its position. In the top-left corner it displays:

        - The current player's turn.
        - The position of the selected piece, if any.
        - The AI's score, as of its last turn.
        - How long the AI's last computation took.
        - The depth to which the AI last searched.

        Parameters
        ----------
        game : :class:`Game`
            The game object to draw information from.

        See Also
        --------
        :class:`env.DEBUG`
        """
        for tile in Board.Tiles:
            surface = self.font_debug.render(f"{tile.x},{tile.y}", True, COLOR_BLACK)
            self.screen.blit(surface, (tile.x * Tile.Size, tile.y * Tile.Size))

        surfaces: list[pygame.Surface] = []

        def print_text(text):
            surfaces.append(self.font_debug.render(text, False, COLOR_WHITE))

        print_text(f"Active player: {game.active_player.name}")
        print_text(f"Selected piece: {game.selected_piece}")
        print_text(f"Computer score: {game.computer_data.achievable_score}")
        print_text(f"Elapsed time: {game.computer_data.compute_time} / {TARGET_TIME}")
        print_text(f"Minimax depth: {game.computer_data.search_depth} / {MINIMUM_DEPTH}")

        width = max(map(pygame.Surface.get_width, surfaces))
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, width, len(surfaces) * self.font_debug.get_height()))
        for y, surface in enumerate(surfaces):
            self.screen.blit(surface, (0, y * self.font_debug.get_height()))
