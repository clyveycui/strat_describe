from src.llm.llm import LanguageModel
from src.llm.llm_schema import StrategyDescription
from src.prompts.prompts import verbalize_main_line_structured_output, verbalize_strategy_structured_output
from src.move_node import MoveNode
from src.chess_utils import bool_to_color_str
import logging

logger = logging.getLogger(__name__)

class LLMVerbalizer:
    def __init__(self, llm : LanguageModel, max_retries : int = 3):
        self.llm = llm
        self.max_retries = max_retries
        
    def sample_verbalized_strategy(self, fen_str, color, strategy, type):
        player_str = bool_to_color_str(color)
        if type == 'main':
            get_verbalized_strategy_prompt = verbalize_main_line_structured_output.format(fen_str=fen_str, player=player_str, principle_line=strategy)
        elif type == 'tree':
            get_verbalized_strategy_prompt = verbalize_strategy_structured_output.format(fen_str=fen_str, player=player_str, strategy=strategy)
        else:
            raise NotImplementedError(f'This type of strategy is not supported. Type: {type}')
        rsps = self.llm.structured_response([get_verbalized_strategy_prompt], schema=StrategyDescription)
        if not rsps:
            logger.warning("No response from LLM")
            return None
        else:
            return rsps[0].description
    
    def verbalize(self, fen_str, color, strategy, type):
        retries = 0
        while retries < self.max_retries:
            description = self.sample_verbalized_strategy(fen_str, color, strategy, type) 
            if description != None:
                break
            retries += 1
        return description
        

