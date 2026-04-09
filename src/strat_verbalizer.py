from src.llm.llm import LanguageModel
from src.llm.llm_schema import StrategyDescription
from src.prompts.prompts import *
import json
from src.chess_utils import bool_to_color_str
import logging

logger = logging.getLogger(__name__)

class LLMVerbalizer:
    def __init__(self, llm : LanguageModel, puzzle_concepts : dict, max_retries : int = 3):
        self.llm = llm
        self.concepts = puzzle_concepts
        self.max_retries = max_retries
        
    def sample_verbalized_strategy(self, fen_str, color, strategy, pid, type):
        player_str = bool_to_color_str(color)
        if type == 'main':
            get_verbalized_strategy_prompt = verbalize_main_line_structured_output.format(fen_str=fen_str, player=player_str, principle_line=strategy)
        elif type == 'tree':
            get_verbalized_strategy_prompt = verbalize_strategy_tree_structured_output.format(fen_str=fen_str, player=player_str, strategy=strategy)
        elif type == 'concept':
            get_verbalized_strategy_prompt = verbalize_strategy_concepts_structured_output.format(fen_str=fen_str, player=player_str, concept=self.concepts[pid])
        elif type == 'tree-concept':
            get_verbalized_strategy_prompt = verbalize_strategy_tree_with_concepts_structured_output.format(fen_str=fen_str, player=player_str, strategy=strategy, concept=self.concepts[pid])
        else:
            raise NotImplementedError(f'This type of strategy is not supported in LLMVerbalizer. Type: {type}')
        rsps = self.llm.structured_response([get_verbalized_strategy_prompt], schema=StrategyDescription)
        if not rsps:
            logger.warning("No response from LLM")
            return None
        else:
            return rsps[0].description
    
    def verbalize(self, fen_str, color, strategy, pid, type):
        retries = 0
        while retries < self.max_retries:
            description = self.sample_verbalized_strategy(fen_str, color, strategy, pid, type) 
            if description != None:
                break
            retries += 1
        return description

#Verbalizer that does not verbalize the strategy, just returns the original strategy in its form
class DirectVerbalizer:
    def __init__(self, puzzle_concepts):
        self.concepts = puzzle_concepts
        
    def verbalize(self, fen_str, color, strategy, pid, type):
        if type == 'json':
            return strategy
        elif type == 'direct-concept':
            return self.concepts[pid]
        else:
            raise NotImplementedError(f'This type of strategy is not supported in DirectVerbalizer. Type: {type}')
        
class FileVerbalizer:
    def __init__(self, path : str):
        self.path = path
        with open(path, 'r') as f:
            s = json.load(f)
        self.strategies = {x['pid'] : x['strat_description'] for x in s}

    def verbalize(self, fen_str, color, strategy, pid, type):
        cached_strategy = self.strategies.get(pid, None)
        if not cached_strategy:
            logger.warning(f'Failed to retrieve strategy for {pid} from {self.path}')
            return ''
        return cached_strategy