import logging

from src.chess_puzzle import ChessPuzzle
from src.move_node import MoveNode
from src.engine import ChessEngine
from src.player import PureLLMPlayer, KBestPlayer, LanguageGuidedLLMPlayer
from src.opponent import Opponent
from src.tree_utils import construct_moves_tree, get_json, get_sequence_of_moves, should_prune
from src.chess_utils import CHECK_MATE_SCORE
from src.llm.llm import LanguageModel
from src.strat_verbalizer import LLMVerbalizer, DirectVerbalizer, FileVerbalizer

from torch.cuda import device_count
import pandas as pd
import argparse
import json
import traceback

logger = logging.getLogger(__name__)

def get_strat(puzzle, puzzle_root, engine, strat_type='main', j=1):
    if strat_type =='main':
        return puzzle.solution
    elif strat_type in ['tree', 'json', 'tree-concept']:
        return get_json(engine.get_strategy(puzzle_root.next_fen, j, puzzle.moves_to_play))

def play_puzzle(puzzle, player, opp_k, opp_d, engine, ref_score, prune_val, strat_type='main', j=1, description_only=False):
    logger.info(f"Playing Puzzle {puzzle.pid}")
    puzzle_root = MoveNode(player=0, board_fen=puzzle.fen, move=puzzle.initial_move_uci, color=not puzzle.solving_player, parent=None)
    opponent = Opponent(k=opp_k, d=opp_d, color=not puzzle.solving_player, engine=engine)
    
    total_moves = 0
    moves_to_play = puzzle.moves_to_play
    prev_node = puzzle_root
    strat_description = None

    if strat_type != 'none':
        strategy = get_strat(puzzle, puzzle_root, engine, strat_type, j)
        logger.info(f"Strategy for puzzle: fen: {puzzle_root.next_fen} strategy: {strategy}")
        strat_description = player.get_description(puzzle_root.next_fen, puzzle.solving_player, strategy, puzzle.pid, type=strat_type)
    if description_only:
        return None, None, None, strat_description
    moves = [prev_node]
    pruned = False
    first_move = True
    try:
        while total_moves < moves_to_play:
            if prev_node.next_player() == 1:
                next_node = player.select_next_move(prev_node)
                if first_move:
                    if should_prune(next_node, prune_val, engine, ref_score):
                        moves = get_sequence_of_moves(next_node, algebraic=False)
                        final_node = next_node
                        pruned = True
                        break
                    first_move = False
                if next_node == None:
                    raise ValueError('LLM player failed to give valid move')
            else: 
                pruned_final_node = construct_moves_tree(prev_node, player, opponent, engine, moves_to_play-total_moves, ref_score, prune_val=prune_val)
                if pruned_final_node != None:
                    moves = get_sequence_of_moves(pruned_final_node, algebraic=False)
                    final_node = pruned_final_node
                    pruned = True
                    break
                next_node = opponent.select_next_move(prev_node)
            moves.append(next_node)
            prev_node = next_node
            final_node = next_node
            total_moves += 1

    except Exception:
        
        logger.warning(f'Puzzle failed with exception {traceback.format_exc()}')
        return None, None, None, strat_description

    return moves, engine.eval_board(final_node.next_fen), pruned, strat_description

def load_puzzles(path, count, start=0):
    puzzles = pd.read_csv(path, nrows=start+count+1, dtype={'PuzzleId': "str"})
    return puzzles[['PuzzleId', 'FEN', 'Moves', 'Themes']][start:count+start]

def load_ref_scores(path):
    scores = pd.read_csv(path, index_col='pid', dtype={'pid': "str"})
    return scores

def load_api(path):
    with open(path, 'r') as f:
        api_key = json.load(f)['openai_api']
    return api_key

def main(args):
    logger.info(f"Starting experiment with parameters: opp_k : {args.opp_k}  opp_d : {args.opp_d} player_k : {args.player_k}, llm : {args.player_llm}")
    engine = ChessEngine()
    puzzles = load_puzzles(args.puzzles_file, args.count, args.start)
    puzzle_concepts = {puzzles.iloc[i]['PuzzleId'] : puzzles.iloc[i]['Themes'].split() for i in range(args.count)}
    ref_scores = load_ref_scores(args.ref_scores)
    if args.player_llm != 'engine':
        if args.player_llm == 'o3':
            llm = LanguageModel('o3', online=True, api_key=load_api('api_key.json'))
        elif args.player_llm == 'openai/gpt-oss-120b':
            llm = LanguageModel('openai/gpt-oss-120b', online=True, api_key='EMPTY', base_url=args.api_base_url)
        elif args.player_llm == 'Qwen/Qwen3-30B-A3B-Thinking-2507':
            llm = LanguageModel('Qwen/Qwen3-30B-A3B-Thinking-2507', online=True, api_key='EMPTY', base_url=args.api_base_url)
        else:
            llm = LanguageModel(args.player_llm, online=False, tensor_parallel_size=args.tensor_parallel_size)
    if args.strat_type in ['json', 'direct-concept']:
        strat_verbalizer = DirectVerbalizer(puzzle_concepts)
    elif args.strat_type in ['tree', 'main', 'concept', 'tree-concept']:
        strat_verbalizer = LLMVerbalizer(llm, puzzle_concepts)
    elif args.strat_type in ['file']:
        if not args.description_path:
            logger.error('Path to description file not provided')
        strat_verbalizer = FileVerbalizer(args.description_path)
        
    if args.player_llm == 'engine':
        player = KBestPlayer(k=1, engine=engine)
    elif args.strat_type == 'none':
        player = PureLLMPlayer(llm)
    else:
        player = LanguageGuidedLLMPlayer(llm, strat_verbalizer)

    res = []
    strat_descriptions = []
    for i in range(args.count):
        pstr = puzzles.iloc[i]
        fen = pstr['FEN']
        main_line = pstr['Moves'].split()
        pid = pstr['PuzzleId']
        ref_score = ref_scores.loc[pid]['eval'].item()
        puzzle = ChessPuzzle(fen, main_line, pid)
        moves, final_eval, pruned, strat_description = play_puzzle(puzzle, player, args.opp_k, args.opp_d, engine, ref_score, prune_val= args.prune_val, strat_type=args.strat_type, j=args.player_k, description_only=args.description_only)
        solving_player = puzzle.solving_player
        res.append([pid, moves, final_eval, solving_player, pruned])
        strat_descriptions.append({'pid': pid, 'strat_description': strat_description})
    res_df = pd.DataFrame(res, columns=['pid', 'moves', 'eval', 'solving_player', 'pruned'])
    out_file = f'../data/results/{args.player_llm.split("/")[-1]}_{args.count}_{args.opp_k}_{args.opp_d}_{args.strat_type}_{args.player_k}{"_" + str(args.prune_val) if args.prune_val != 2* CHECK_MATE_SCORE else ""}.csv'
    res_df.to_csv(out_file)
    with open(f'../data/results/descr_{args.player_llm.split("/")[-1]}_{args.count}_{args.opp_k}_{args.opp_d}_{args.strat_type}_{args.player_k}{"_" + str(args.prune_val) if args.prune_val != 2* CHECK_MATE_SCORE else ""}.json', 'w') as f:
        json.dump(strat_descriptions, f, indent=4)
    
if __name__ ==  '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--puzzles_file', type=str, default='../data/lichess_db_puzzle.csv')
    args_parser.add_argument('--ref_scores', type=str, default='../data/results/ref_50.csv')
    args_parser.add_argument('--count', type=int, default=30)
    args_parser.add_argument('--start', type=int, default=0)
    args_parser.add_argument('--player_llm', type=str, default="engine")
    args_parser.add_argument('--opp_k', type=int, default=1)
    args_parser.add_argument('--opp_d', type=int, default=1)
    args_parser.add_argument('--player_k', type=int, default=1)
    args_parser.add_argument('--strat_type', type=str, choices=['none', 'main', 'tree', 'json', 'file', 'direct-concept', 'concept', 'tree-concept'], default='none')
    args_parser.add_argument('--prune_val', type=int, default = 2 * CHECK_MATE_SCORE)
    args_parser.add_argument('--description_path', type=str, default = None)
    args_parser.add_argument('--tensor_parallel_size', type=int, default = 1)
    args_parser.add_argument('--api_base_url', type=str, default = 'http://localhost:8000/v1')
    args_parser.add_argument('--description_only', action='store_true', default=False)
        
    args = args_parser.parse_args()
    log_file = f'../data/logs/{args.player_llm.split("/")[-1]}_{args.count}_{args.opp_k}_{args.opp_d}_{args.strat_type}_{args.player_k}{"_"  + str(args.prune_val) if args.prune_val != 2* CHECK_MATE_SCORE else ""}.log'
    logging.basicConfig(filename=log_file, format="%(asctime)s - %(levelname)s : %(message)s", encoding='utf-8', level=logging.INFO)
    
    main(args)