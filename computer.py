from __future__ import annotations
from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from checkers import Board, Player, vec2
from env import DEBUG, TARGET_TIME, MINIMUM_DEPTH

import math
import time
import cProfile
from collections import defaultdict
from dataclasses import dataclass
from scipy.optimize import curve_fit


@dataclass
class Tile:
    _value: str


def get_moves(board: Board, player: Player, locked_piece: vec2 = None) -> tuple[bool, defaultdict[vec2, list[vec2]]]:
    """Generate all possible moves for a player, with respect to a locked piece.

    This function is essentially the same as :meth:`~checkers.Game.generate_moves`, but without an encapsulating Game object.

    Parameters
    ----------
    board : :class:`~checkers.Board`
        The board to generate moves for.
    player : :class:`~checkers.Player`
        The player to generate moves for.
    locked_piece : :class:`~checkers.vec2`, optional
        A piece which has already captured this turn.

    Returns
    -------
    ``bool``
        Whether or the generated moves are capturing.
    ``defaultdict[vec2, list[vec2]]``
        A mapping of pieces to their possible moves.
    """
    capturing_moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
    all_moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
    for tile in [locked_piece] if locked_piece else board.get_player_pieces(player):
        for move, capturing in board.get_piece_moves(tile):
            if capturing:
                capturing_moves[tile].append(move)
            all_moves[tile].append(move)
    if capturing_moves:
        return True, capturing_moves
    return False, (defaultdict(list) if locked_piece else all_moves)


def get_subsequent_moves(next_board: Board, player: Player, compound_move: list[vec2]) -> Generator[list[vec2]]:
    """The recursive step of :func:`get_compound_moves`."""
    next_board.move(*compound_move[-2:])
    capturing, all_next_moves = get_moves(next_board, player, compound_move[-1])
    if not capturing:
        move = compound_move[-1]
        if move.y in (0, 7) and not next_board.get(move).piece.king:
            next_board.set(move, Tile("a" if player == player.ONE else "b"))
        yield compound_move, next_board
    else:
        next_piece, next_moves = list(all_next_moves.items())[0]
        for next_move in next_moves:
            yield from get_subsequent_moves(next_board.copy(), player, compound_move + [next_move])


def get_compound_moves(board: Board, player: Player) -> Generator[tuple[list[vec2], Board]]:
    """Generate all possible sequences of moves for a player.

    This function starts by generating all possible moves, if there are capturing moves,
    it will generate all possible moves from those positions and so on until there are no more moves.
    This function also takes care of turning normal pieces into kings if they reach the opposite side.

    Parameters
    ----------
    board : :class:`~checkers.Board`
        The board to generate moves for.
    player : :class:`~checkers.Player`
        The player to generate moves for.

    Yields
    -------
    ``list[vec2]``
        A starting position and then a sequence of positions a piece can, in order, jump to.
    :class:`~checkers.Board`
        The state of the board after executing the sequence of moves.
    """
    capturing, all_moves = get_moves(board, player)
    for piece, moves in all_moves.items():
        for move in moves:
            base_board = board.copy()
            base_move = [piece, move]

            if capturing:
                yield from get_subsequent_moves(base_board, player, base_move)
            else:
                base_board.move(*base_move)
                if move.y in (0, 7) and not base_board.get(move).piece.king:
                    base_board.set(move, Tile("a" if player == player.ONE else "b"))
                yield base_move, base_board


cache = {}
cached = 0


def minimax(board: Board, player: Player, depth: int = 7, maximizing: bool = True, alpha: float = -float('inf'), beta: float = float('inf')) -> tuple[float, list[vec2]]:
    """The main decision function of the AI.

    An alpha-beta pruning minimax algorithm is used to iterate over all possible board states, to a certain depth.
    When it reaches the max depth or a game end the board state is scored and returned.
    Caches scores for end board states to speed up the algorithm.

    Parameters
    ----------
    board : :class:`~checkers.Board`
        The board to generate moves from.
    player : :class:`~checkers.Player`
        The computer player.
    depth : ``int``, default ``7``
        The depth to search to.
    maximizing : ``bool``, default ``True``
        Whether the current iteration's player is trying to maximize or minimize the score.
    alpha : ``float``, default ``-float('inf')``
        The alpha value for pruning.
    beta : ``float``, default ``float('inf')``
        The beta value for pruning.

    Returns
    -------
    ``float``
        The best score for the current player.
    ``list[vec2]``
        A sequence of moves towards the best score.

    See Also
    --------
    :meth:`~checkers.Board.score`
    """    
    global cached
    if board.grid in cache:
        cached += 1
        return cache[board.grid], []

    if DEBUG >= 3:
        print(f"{' ' * (5 - depth)}{depth}\t{maximizing}\t{alpha}\t{beta}\t{board.score(player)}\t{board.grid}")

    if not next(board.get_player_pieces(player), False):
        return -1000 - depth, []
    if not next(board.get_player_pieces(player.other()), False):
        return 1000 + depth, []
    if depth == 0:
        score = board.score(player)
        cache[board.grid] = score
        return score, []

    if maximizing:
        best = (-2000 + depth, [])
        for compound_move, next_board in get_compound_moves(board, player):
            score = minimax(next_board, player, depth - 1, False, alpha, beta)[0]
            alpha = max(alpha, score)
            if score > best[0]:
                best = (score, compound_move)
            if score >= beta:
                break
        return best
    else:
        best = (2000 - depth, [])
        for compound_move, next_board in get_compound_moves(board, player.other()):
            score = minimax(next_board, player, depth - 1, True, alpha, beta)[0]
            beta = min(beta, score)
            if score < best[0]:
                best = (score, compound_move)
            if score <= alpha:
                break
        return best


depth = MINIMUM_DEPTH
samples = []


@dataclass
class ComputerData:
    """Holds the AI's resulting data."""
    compound_move: list[tuple[vec2, vec2]]
    """The sequence of moves the AI made."""
    achievable_score: int
    """The best score found using the minimax algorithm."""
    compute_time: int
    """The time it took to compute the result."""
    search_depth: int
    """The depth of the minimax search."""


def run(board: Board, player: Player) -> ComputerData:
    """The AI's interface.

    Runs the minimax algorithm and returns the result.

    Supported debugging levels:
        - ``0``: No debugging.
        - ``1``: Prints the algorithm timing. Prints the visited end node count, cached end node count, and the best score.
        - ``2``: Profiles the algorithm.
        - ``3``: Dumps data for each visited node.

    Parameters
    ----------
    board : :class:`~checkers.Board`
        The board to run the AI on.
    player : :class:`~checkers.Player`
        The player to run the AI as.

    Returns
    -------
    :class:`ComputerData`
        The resulting data.

    See Also
    --------
    :func:`minimax`
    """
    global cache, cached, depth
    cache = {}
    cached = 0

    start = time.time()
    if DEBUG >= 2:
        with cProfile.Profile() as prof:
            prof.enable()
            if DEBUG >= 3:
                print(f"DEPTH\tMAX\tALPHA\tBETA\tSCORE\tGRID")
            score, moves = minimax(board, player, depth)
            prof.disable()
            prof.print_stats("cumtime")
    else:
        score, moves = minimax(board, player, depth)

    elapsed = (time.time() - start) * 1000
    samples.append((depth, elapsed))
    def func(x, a): return a ** x
    if len(samples) > 1:
        (factor,), _ = curve_fit(func, *zip(*samples[-5:]))
        depth = max(MINIMUM_DEPTH, int(math.log(TARGET_TIME, factor)))

    if DEBUG >= 1:
        print(f"{cached} cached / {len(cache)} new - {elapsed * 1000:.2f}ms, best {score}")
        print(moves)

    return ComputerData(list(zip(moves, moves[1:])), score, int(elapsed), depth)
