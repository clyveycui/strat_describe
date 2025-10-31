import logging

from src.llm.llm import LanguageModel
from src.llm.llm_schema import Move
from src.prompts.prompts import *
from src.chess_utils import validate_move, bool_to_color_str
from src.move_node import MoveNode
from src.engine import ChessEngine
from src.tree_utils import get_sequence_of_moves

logger = logging.getLogger(__name__)

class PureLLMPlayer:
    def __init__(self, llm : LanguageModel, max_retries : int = 3):
        self.llm = llm
        self.max_retries = max_retries
    
    def sample_next_move(self, fen_str, color, previous_tries = []):
        player_str = bool_to_color_str(color)
        retry_warning = '' if len(previous_tries) == 0 else illegal_moves_str.format(illegal_moves=previous_tries)
        get_move_prompt = pure_LLM_get_next_move_prompt_structured_output.format(illegal_moves=retry_warning, fen_str=fen_str, player=player_str)
        rsps = self.llm.structured_response([get_move_prompt], schema=Move)
        if not rsps:
            logger.warning("No response from LLM")
            return None
        else:
            return rsps[0].move[:4]

    def get_next_moves(self, prev_node: MoveNode):
        fen_str = prev_node.next_fen
        color = not prev_node.color
        previous_tries = []

        while len(previous_tries) < self.max_retries:
            next_move = self.sample_next_move(fen_str, color, previous_tries)
            if next_move == None: #LLM not giving a output, should abort
                return None
            if validate_move(fen_str, next_move): #valid next move
                return [next_move]
            else: #Illegal move, retry
                previous_tries.append(next_move)
        logger.warning("Failed to get a valid next move from LLM")
        return None
    
    def select_next_move(self, prev_node: MoveNode):
        assert prev_node.player == 0
        if prev_node.has_children():
            assert len(prev_node.children) == 1
            return prev_node.children[0]

        next_move = self.get_next_moves(prev_node)
        if next_move == None:
            return None
        next_move = next_move[0]
        node = MoveNode(player=1, board_fen=prev_node.next_fen, move=next_move, color=not prev_node.color, parent=prev_node)
        return node
    
class LanguageGuidedLLMPlayer:
    def __init__(self, llm : LanguageModel, strat_verbalizer, max_retries : int = 3, conversational: bool=False):
        self.llm = llm
        self.max_retries = max_retries
        self.conversational = conversational
        self.strat_verbalizer = strat_verbalizer
        self.description = None
        
    def get_description(self, fen_str, color, strategy, type: str ='main'):
        description = self.strat_verbalizer.verbalize(fen_str, color, strategy, type)
        self.description = description
        return description
        
    def sample_next_move(self, fen_str, color, previous_moves, previous_tries = []):
        if self.description == None:
            logger.warning("No description of strategy is provided")
        player_str = bool_to_color_str(color)
        retry_warning = '' if len(previous_tries) == 0 else illegal_moves_str.format(illegal_moves=previous_tries)
        if not self.conversational:
            get_move_prompt = guided_LLM_stateless_get_next_move_prompt_structured_output.format(illegal_moves=retry_warning, fen_str=fen_str, player=player_str, prev_moves=previous_moves, strat_str=self.description)
        else:
            raise NotImplementedError('Conversational Mode not implemented')
        rsps = self.llm.structured_response([get_move_prompt], schema=Move)
        if not rsps:
            logger.warning("No response from LLM")
            return None
        else:
            return rsps[0].move[:4]

    def get_next_moves(self, prev_node: MoveNode):
        fen_str = prev_node.next_fen
        color = not prev_node.color
        previous_moves = get_sequence_of_moves(prev_node)
        previous_tries = []
        while len(previous_tries) < self.max_retries:
            next_move = self.sample_next_move(fen_str, color, previous_moves, previous_tries)
            if next_move == None: #LLM not giving a output, should abort
                return None
            if validate_move(fen_str, next_move): #valid next move
                return [next_move]
            else: #Illegal move, retry
                previous_tries.append(next_move)
        logger.warning("Failed to get a valid next move from LLM")
        return None
    
    def select_next_move(self, prev_node: MoveNode):
        assert prev_node.player == 0
        if prev_node.has_children():
            assert len(prev_node.children) == 1
            return prev_node.children[0]

        next_move = self.get_next_moves(prev_node)
        if next_move == None:
            return None
        next_move = next_move[0]
        node = MoveNode(player=1, board_fen=prev_node.next_fen, move=next_move, color=not prev_node.color, parent=prev_node)
        return node

class EngineGuidedLLMPlayer:
    def __init__(self):
        pass

    
    
class KBestPlayer:
    #k: number of variations to explore.
    #d: number of steps to forsee. 1 means player plays 1 move. 2 means player plays 2 moves etc.
    def __init__(self, k, engine: ChessEngine):
        self.k = k
        self.engine = engine
    
    #Returns the set of candidate moves
    def get_next_moves(self, fen_str, color):
        best_moves = self.engine.get_top_moves(fen=fen_str, k=self.k)
        return [best_moves[self.k - 1]['Move']]
    
    #Select the move that maximally exploit the opposing player
    def select_next_move(self, prev_node: MoveNode):
        assert prev_node.player == 0
        if prev_node.has_children():
            assert len(prev_node.children) == 1
            return prev_node.children[0]

        next_move = self.get_next_moves(prev_node.next_fen, prev_node.color)[0]
        if next_move == None:
            return None
        
        node = MoveNode(player=1, board_fen=prev_node.next_fen, move=next_move, color=not prev_node.color, parent=prev_node)
        prev_node.add_children([node])
        return node