from src.llm.llm import LanguageModel
from src.llm.llm_schema import StrategyDescription
from src.prompts.prompts import verbalize_main_line_structured_output

import logging

logger = logging.getLogger(__name__)

class LLMVerbalizer:
    def __init__(self, llm : LanguageModel, max_retries : int = 3):
        self.llm = llm
        self.max_retries = max_retries
        
    def sample_verbalized_strategy(self, fen_str, color, main_line):
        player_str = 'white' if color else 'black'
        get_move_prompt = verbalize_main_line_structured_output.format(fen_str=fen_str, player=player_str, principle_line=main_line)
        rsps = self.llm.structured_response([get_move_prompt], schema=StrategyDescription)
        if not rsps:
            logger.warning("No response from LLM")
            return None
        else:
            return rsps[0].description
    
    #Takes in a list of moves, verbalizes it to the 
    def verbalize_main_line(self, fen_str: str, color: bool, main_line: list):
        retries = 0
        while retries < self.max_retries:
            description = self.sample_verbalized_strategy(fen_str, color, main_line) 
            if description != None:
                break
            retries += 1
        return description
    
    def verbalize(self, fen_str, color, strategy, type):
        if type == 'main':
            return self.verbalize_main_line(fen_str, color, strategy)
        else:
            raise NotImplementedError(f'This type of strategy is not supported. Type: {type}')