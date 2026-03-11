import sqlite3
import json
import os
import sys
import chess
import numpy as np
import pandas as pd
from collections import deque

# Allow imports from strat_describe
from src.engine import ChessEngine
from src.chess_utils import get_next_fen, get_color_from_fen, CHECK_MATE_SCORE


# ---------------------------------------------------------------------------
# Existing helpers
# ---------------------------------------------------------------------------

def sigmoid(x):
    if pd.isna(x):
        return np.nan
    if x == -CHECK_MATE_SCORE:
        return 0.0
    if x == CHECK_MATE_SCORE:
        return 1.0
    return 1.0 / (1.0 + np.power(10.0, -x / 400.0))


def get_results(path, puzzle_file):
    scores = pd.read_csv(path)
    count = len(scores)
    puzzles = pd.read_csv(puzzle_file, nrows=count)
    player = puzzles['FEN'].apply(get_color_from_fen)
    scores = scores['eval'].apply(sigmoid)
    scores = scores.where(player != True, other=1 - scores)
    return scores.mean(skipna=True)


# ---------------------------------------------------------------------------
# Survey evaluation
# ---------------------------------------------------------------------------

def _normalize_fen(fen: str) -> str:
    """Return only the board/color/castling/en-passant fields, ignoring clocks."""
    return ' '.join(fen.split()[:4])


def _load_responses(db_path: str, email: str, puzzle_id: str) -> dict[int, str]:
    """Return {board_index: move_uci} for the given participant and puzzle."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT r.board_index, r.move_uci
            FROM responses r
            JOIN users u ON u.session_id = r.session_id
            WHERE u.email = ? AND r.puzzle_id = ?
            """,
            (email, puzzle_id),
        ).fetchall()
    return {row['board_index']: row['move_uci'] for row in rows}


def _evaluate_puzzle(fens: list[str], responses: dict[int, str], engine: ChessEngine, opp_k: int = 3) -> int:
    """
    Walk the puzzle BFS tree, verifying each player response against the engine's
    best move.  Returns the worst centipawn score for the player across all tree
    paths (oriented so that higher = better for the player regardless of colour).

    Tree structure
    --------------
    Every FEN in *fens* is a position where the player must respond (BFS order,
    the same ordering produced by build_puzzle_trees.py).  At each node:
      - Correct move  → follow the opponent's top-K responses as child nodes.
      - Wrong move    → evaluate the resulting position; truncate the branch.
      - No response   → evaluate the current position; truncate the branch.
      - Leaf node     → evaluate the resulting position after the player's move.
    """
    # Build normalised-FEN → index map (first occurrence wins for near-duplicates)
    norm_to_idx: dict[str, int] = {}
    for i, fen in enumerate(fens):
        norm = _normalize_fen(fen)
        if norm not in norm_to_idx:
            norm_to_idx[norm] = i

    player_is_white = get_color_from_fen(fens[0])

    def orient(raw_cp: int) -> int:
        """Convert engine centipawns (white-positive) to player-positive."""
        return raw_cp #if player_is_white else -raw_cp

    leaf_scores: list[int] = []
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(fens[0], 0)])

    while queue:
        fen, idx = queue.popleft()
        norm = _normalize_fen(fen)
        if norm in visited:
            continue
        visited.add(norm)

        player_move = responses.get(idx)

        # --- No response recorded: penalise with current position score ---
        if player_move is None:
            leaf_scores.append(orient(engine.eval_board(fen)))
            continue

        # --- Fetch engine's best move ---
        top_moves = engine.get_top_moves(fen, 1)
        best_move = top_moves[0]['Move'] if top_moves else None

        result_fen = get_next_fen(fen, player_move)

        # --- Wrong move: evaluate and truncate ---
        if player_move != best_move:
            leaf_scores.append(orient(engine.eval_board(result_fen)))
            continue

        # --- Correct move: look for children ---
        board_after = chess.Board(result_fen)
        if board_after.is_game_over():
            # Player delivered checkmate / caused stalemate — best outcome
            leaf_scores.append(orient(CHECK_MATE_SCORE))
            continue

        top_opp = engine.get_top_moves(result_fen, opp_k)
        children_added = 0
        for opp in top_opp:
            b2 = chess.Board(result_fen)
            b2.push_uci(opp['Move'])
            if b2.is_game_over():
                continue
            child_norm = _normalize_fen(b2.fen())
            child_idx = norm_to_idx.get(child_norm)
            if child_idx is not None and child_norm not in visited:
                queue.append((b2.fen(), child_idx))
                children_added += 1

        # --- Leaf at max depth with correct move: evaluate result ---
        if children_added == 0:
            leaf_scores.append(orient(engine.eval_board(result_fen)))

    # No evaluable leaves means the player answered nothing — treat as worst case
    return min(leaf_scores) if leaf_scores else -CHECK_MATE_SCORE


def evaluate_participant(
    db_path: str,
    email: str,
    puzzle_ids: list[str],
    puzzles_json_path: str,
    opp_k: int = 3,
    stockfish_path: str | None = None,
) -> tuple[dict[str, int], float]:
    """
    Evaluate a survey participant's performance across the given puzzles.

    Parameters
    ----------
    db_path          : path to survey.db
    email            : participant email address
    puzzle_ids       : list of puzzle IDs to evaluate
    puzzles_json_path: path to the puzzle JSON file (puzzles_A.json / puzzles_B.json)
    opp_k            : opponent branching factor (default 3, must match survey generation)
    stockfish_path   : optional path to Stockfish binary

    Returns
    -------
    scores           : dict mapping puzzle_id → worst oriented centipawn score
    normalized_score : float in [0, 1]; average sigmoid of per-puzzle worst scores,
                       where 1.0 = perfect play on every puzzle
    """
    with open(puzzles_json_path) as f:
        puzzle_map = {p['puzzle_id']: p for p in json.load(f)}

    engine = ChessEngine(stockfish_path)

    scores: dict[str, int] = {}
    for pid in puzzle_ids:
        if pid not in puzzle_map:
            continue
        puzzle = puzzle_map[pid]
        responses = _load_responses(db_path, email, pid)
        scores[pid] = _evaluate_puzzle(puzzle['fen'], responses, engine, opp_k=opp_k)

    sig_scores = [sigmoid(s) for s in scores.values()]
    normalized = float(np.mean(sig_scores)) if sig_scores else float('nan')

    return scores, normalized
