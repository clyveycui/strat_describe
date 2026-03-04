from src.chess_puzzle import ChessPuzzle
from src.engine import ChessEngine
from src.chess_utils import get_next_fen

import pandas as pd
import argparse

def load_puzzles(path, count):
    puzzles = pd.read_csv(path, nrows=count+1)
    return puzzles[['PuzzleId', 'FEN', 'Moves']]

def main(args):
    engine = ChessEngine()
    puzzles = load_puzzles(args.puzzles_file, args.count)
    res = []
    for i in range(args.count):
        pstr = puzzles.iloc[i]
        fen = pstr['FEN']
        main_line = pstr['Moves'].split()
        pid = pstr['PuzzleId']
        puzzle = ChessPuzzle(fen, main_line, pid)
        next_fen = fen
        for move in main_line:
            next_fen = get_next_fen(next_fen, move)
        final_fen = next_fen
        score = engine.eval_board(final_fen)
        solving_player = puzzle.solving_player
        res.append([pid, main_line, score, solving_player, False])
    res_df = pd.DataFrame(res, columns=['pid', 'moves', 'eval', 'solving_player', 'pruned'])
    out_file = f'../data/results/ref_{args.puzzles_file.split("/")[-1].split(".")[0]}.csv'
    res_df.to_csv(out_file)
    
if __name__ ==  '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--puzzles_file', type=str, default='../data/sampled_30_rows.csv')
    args_parser.add_argument('--count', type=int, default=30)
    
    args = args_parser.parse_args()
    main(args)