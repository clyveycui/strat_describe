import logging

from src.chess_puzzle import ChessPuzzle
from src.move_node import MoveNode
from src.engine import ChessEngine
from src.player import PureLLMPlayer, KBestPlayer
from src.opponent import Opponent
from src.tree_utils import construct_moves_tree
from src.llm.llm import LanguageModel

from torch.cuda import device_count
import pandas as pd
import argparse
import json

logger = logging.getLogger(__name__)


def play_puzzle(puzzle, player, opp_k, opp_d, engine):
    puzzle_root = MoveNode(player=0, board_fen=puzzle.fen, move=puzzle.initial_move_uci, color=not puzzle.solving_player, parent=None)
    opponent = Opponent(k=opp_k, d=opp_d, color=not puzzle.solving_player, engine=engine)
    
    total_moves = 0
    moves_to_play = puzzle.moves_to_play
    prev_node = puzzle_root

    moves = [prev_node]
    try:
        while total_moves < moves_to_play:

            if prev_node.next_player() == 1:
                next_node = player.select_next_move(prev_node)
                if next_node == None:
                    raise ValueError('LLM player failed to give valid move')
            else: 
                construct_moves_tree(prev_node, player, opponent, moves_to_play-total_moves)
                next_node = opponent.select_next_move(prev_node)
            moves.append(next_node)
            prev_node = next_node
            total_moves += 1
    except Exception as e:
        logger.warning(f'Puzzle failed with exception {e}')
        return None, None

    return moves, engine.eval_board(prev_node.next_fen)

def load_puzzles(path, count):
    puzzles = pd.read_csv(path, nrows=count+1)
    return puzzles[['PuzzleId', 'FEN', 'Moves']]

def load_api(path):
    with open(path, 'r') as f:
        api_key = json.load(f)['openai_api']
    return api_key

def main(args):
    engine = ChessEngine()
    puzzles = load_puzzles(args.puzzles_file, args.count)
    # llm = LanguageModel(args.player_llm, online=True, api_key=load_api('api_key.json'))
    # player = PureLLMPlayer(llm)
    player = KBestPlayer(k=1, engine=engine)
    res = []
    for i in range(args.count):
        pstr = puzzles.iloc[i]
        fen = pstr['FEN']
        main_line = pstr['Moves'].split()
        pid = pstr['PuzzleId']
        puzzle = ChessPuzzle(fen, main_line)
        moves, final_eval = play_puzzle(puzzle, player, args.opp_k, args.opp_d, engine)
        res.append([pid, moves, final_eval])
    res_df = pd.DataFrame(res, columns=['pid', 'moves', 'eval'])
    res_df.to_csv(args.res_out)

if __name__ ==  '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--puzzles_file', type=str, default='./data/puzzles/lichess_db_puzzle.csv')
    args_parser.add_argument('--count', type=int, default=1000)
    args_parser.add_argument('--player_llm', type=str, default="o3")
    args_parser.add_argument('--log', type=str, default='out.log')
    args_parser.add_argument('--opp_k', type=int, default=1)
    args_parser.add_argument('--opp_d', type=int, default=1)
    args_parser.add_argument('--res_out', type=str, default='./data/results/Qwen_2000_1_1.csv')
    
    args = args_parser.parse_args()
    
    logging.basicConfig(filename=args.log, format="%(asctime)s - %(levelname)s : %(message)s", encoding='utf-8', level=logging.INFO)
    
    main(args)