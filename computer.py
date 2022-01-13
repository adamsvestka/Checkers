from __future__ import annotations
import time
from functools import cached_property
from typing import TYPE_CHECKING, Generator
if TYPE_CHECKING:
    from checkers import Board, Player, vec2

from collections import defaultdict


def get_moves(board: Board, player: Player, locked_piece: vec2 = None) -> tuple[bool, defaultdict[vec2, list[vec2]]]:
    capturing_moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
    all_moves: defaultdict[vec2, list[vec2]] = defaultdict(list)
    for tile in [locked_piece] if locked_piece else board.get_player_pieces(player):
        for move in board.get_piece_moves(tile):
            if move.distance(tile) == 2:
                capturing_moves[tile].append(move)
            all_moves[tile].append(move)
    if capturing_moves:
        return True, capturing_moves
    return False, (defaultdict(list) if locked_piece else all_moves)


def get_compound_moves(board: Board, player: Player) -> Generator[tuple[list[vec2], Board]]:
    capturing, all_moves = get_moves(board, player)
    for piece, moves in all_moves.items():
        for move in moves:
            base_board = board.copy()
            base_move = [piece, move]

            def recurse(next_board: Board, compound_move: list[vec2]) -> Generator[list[vec2]]:
                next_board.move(*compound_move[-2:])
                capturing, all_next_moves = get_moves(next_board, player, compound_move[-1])
                if not capturing:
                    yield compound_move, next_board
                else:
                    next_piece, next_moves = list(all_next_moves.items())[0]
                    for next_move in next_moves:
                        yield from recurse(next_board.copy(), compound_move + [next_move])

            if capturing:
                yield from recurse(base_board, base_move)
            else:
                base_board.move(*base_move)
                yield base_move, base_board


def algorithm(board: Board, player: Player):
    best = (-float('inf'), None)
    for compound_move, next_board in get_compound_moves(board, player):
        score = next_board.score(player)
        if score > best[0]:
            best = (score, compound_move)
    return best[1]


cache = {}
cached = 0


def minimax(board: Board, player: Player, depth: int = 3, maximizing: bool = True, alpha: float = -float('inf'), beta: float = float('inf')) -> tuple[float, list[vec2]]:
    global cached
    if board.grid in cache:
        cached += 1
        return cache[board.grid], []
    if depth == 0:
        score = board.score(player)
        cache[board.grid] = score
        return score, []
    if maximizing:
        best = (-float('inf'), [])
        for compound_move, next_board in get_compound_moves(board, player):
            score = minimax(next_board, player, depth - 1, False, alpha, beta)[0]
            alpha = max(alpha, score)
            if score > best[0]:
                best = (score, compound_move)
            if score >= beta:
                break
        return best
    else:
        best = (float('inf'), [])
        for compound_move, next_board in get_compound_moves(board, player):
            score = minimax(next_board, player, depth - 1, True, alpha, beta)[0]
            beta = min(beta, score)
            if score < best[0]:
                best = (score, compound_move)
            if score <= alpha:
                break
        return best


def run(board: Board, player: Player) -> list[tuple[vec2, vec2]]:
    global cache, cached
    cache = {}
    cached = 0

    start = time.time()
    score, moves = minimax(board, player, 5, False)

    print(f"{cached} cached / {len(cache)} new - {(time.time() - start) * 1000:.2f}ms : score {score}")
    print(*cache.values())

    return list(zip(moves, moves[1:]))
