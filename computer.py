from __future__ import annotations
from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from checkers import Board, Player, vec2

import math
import time
import cProfile
from collections import defaultdict
from dataclasses import dataclass
from scipy.optimize import curve_fit
from os import environ

# 0: normal, 1: timing, 2: profiling, 3: dump
DEBUG = int(environ.get("DEBUG", "0"))


@dataclass
class Tile:
    _value: str


def get_moves(board: Board, player: Player, locked_piece: vec2 = None) -> tuple[bool, defaultdict[vec2, list[vec2]]]:
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


def recurse(next_board: Board, player: Player, compound_move: list[vec2]) -> Generator[list[vec2]]:
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
            yield from recurse(next_board.copy(), player, compound_move + [next_move])


def get_compound_moves(board: Board, player: Player) -> Generator[tuple[list[vec2], Board]]:
    capturing, all_moves = get_moves(board, player)
    for piece, moves in all_moves.items():
        for move in moves:
            base_board = board.copy()
            base_move = [piece, move]

            if capturing:
                yield from recurse(base_board, player, base_move)
            else:
                base_board.move(*base_move)
                if move.y in (0, 7) and not base_board.get(move).piece.king:
                    base_board.set(move, Tile("a" if player == player.ONE else "b"))
                yield base_move, base_board


cache = {}
cached = 0


def minimax(board: Board, player: Player, depth: int = 7, maximizing: bool = True, alpha: float = -float('inf'), beta: float = float('inf')) -> tuple[float, list[vec2]]:
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


target_duration = 1500
samples = []
depth = 7


def run(board: Board, player: Player) -> tuple[list[tuple[vec2, vec2]], int, int, int]:
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

    if DEBUG >= 1:
        print(f"{cached} cached / {len(cache)} new - {(time.time() - start) * 1000:.2f}ms, best {score}")
        print(moves)

    elapsed = (time.time() - start) * 1000
    samples.append((depth, elapsed))
    def func(x, a): return a ** x
    (factor,), _ = curve_fit(func, *zip(*samples[-5:]))
    depth = max(5, int(math.log(target_duration, factor)))

    return list(zip(moves, moves[1:])), score, int(elapsed), depth
