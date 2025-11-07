import logging

from src.chess_puzzle import ChessPuzzle
from src.move_node import MoveNode
from src.engine import ChessEngine
from src.player import PureLLMPlayer, KBestPlayer, LanguageGuidedLLMPlayer
from src.opponent import Opponent
from src.tree_utils import construct_moves_tree, get_json
from src.llm.llm import LanguageModel
from src.strat_verbalizer import LLMVerbalizer, DirectVerbalizer

from torch.cuda import device_count
import pandas as pd
import argparse
import json
import traceback

logger = logging.getLogger(__name__)

def get_strat(puzzle, puzzle_root, engine, strat_type='main', j=1):
    if strat_type =='main':
        return puzzle.solution
    elif strat_type =='tree' or strat_type == 'json':
        return get_json(engine.get_strategy(puzzle_root.next_fen, j, puzzle.moves_to_play))

def play_puzzle(puzzle, player, opp_k, opp_d, engine, strat_type='main', j=1):
    logger.info(f"Playing Puzzle {puzzle.pid}")
    puzzle_root = MoveNode(player=0, board_fen=puzzle.fen, move=puzzle.initial_move_uci, color=not puzzle.solving_player, parent=None)
    opponent = Opponent(k=opp_k, d=opp_d, color=not puzzle.solving_player, engine=engine)
    
    total_moves = 0
    moves_to_play = puzzle.moves_to_play
    prev_node = puzzle_root
    
    strategy = get_strat(puzzle, puzzle_root, engine, strat_type, j)

    logger.info(f"Strategy for puzzle: fen: {puzzle_root.next_fen} strategy: {strategy}")
    player.get_description(puzzle_root.next_fen, puzzle.solving_player, strategy, type=strat_type)

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
    except Exception:
        
        logger.warning(f'Puzzle failed with exception {traceback.format_exc()}')
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
    logger.info(f"Starting experiment with parameters: opp_k : {args.opp_k}  opp_d : {args.opp_d} player_k : {args.player_k}, llm : {args.player_llm}")
    engine = ChessEngine()
    puzzles = load_puzzles(args.puzzles_file, args.count)
    llm = LanguageModel(args.player_llm, online=True, api_key=load_api('api_key.json'))
    #strat_verbalizer = LLMVerbalizer(llm)
    strat_verbalizer = DirectVerbalizer()
    player = LanguageGuidedLLMPlayer(llm, strat_verbalizer)
    #player = PureLLMPlayer(llm)
    #player = KBestPlayer(k=1, engine=engine)
    res = []
    for i in range(args.count):
        pstr = puzzles.iloc[i]
        fen = pstr['FEN']
        main_line = pstr['Moves'].split()
        pid = pstr['PuzzleId']
        puzzle = ChessPuzzle(fen, main_line, pid)
        moves, final_eval = play_puzzle(puzzle, player, args.opp_k, args.opp_d, engine, strat_type=args.strat_type, j=args.player_k)
        solving_player = puzzle.solving_player
        res.append([pid, moves, final_eval, solving_player])
    res_df = pd.DataFrame(res, columns=['pid', 'moves', 'eval', 'solving_player'])
    out_file = f'./data/results/{args.player_llm}_{args.count}_{args.opp_k}_{args.opp_d}_{args.strat_type}_{args.player_k}.csv'
    res_df.to_csv(out_file)
    
if __name__ ==  '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--puzzles_file', type=str, default='./data/puzzles/lichess_db_puzzle.csv')
    args_parser.add_argument('--count', type=int, default=50)
    args_parser.add_argument('--player_llm', type=str, default="o3")
    args_parser.add_argument('--opp_k', type=int, default=1)
    args_parser.add_argument('--opp_d', type=int, default=1)
    args_parser.add_argument('--player_k', type=int, default=1)
    args_parser.add_argument('--strat_type', type=str, default='main')
    
    args = args_parser.parse_args()
    log_file = f'./data/logs/{args.player_llm}_{args.count}_{args.opp_k}_{args.opp_d}_{args.strat_type}_{args.player_k}.log'
    logging.basicConfig(filename=log_file, format="%(asctime)s - %(levelname)s : %(message)s", encoding='utf-8', level=logging.INFO)
    
    main(args)