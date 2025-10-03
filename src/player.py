import logging

from src.llm.llm import LanguageModel
from src.llm.llm_schema import Move
from src.chess_puzzle import ChessPuzzle
from src.prompts.prompts import *

logger = logging.getLogger(__name__)

class PureLLMPlayer:
    def __init__(self, llm : LanguageModel, max_retries : int = 3):
        self.llm = llm
        self.max_retries = max_retries
    
    def get_next_move(self, fen_str, player, previous_tries = []):
        player_str = 'white' if player else 'black'
        retry_warning = None if len(previous_tries) == 0 else illegal_moves_str.format(illegal_moves=previous_tries)
        get_move_prompt = pure_LLM_get_next_move_prompt_structured_output.format(illegal_moves=retry_warning, fen=fen_str, player=player_str)
        rsps = self.llm.structured_response(get_move_prompt, schema=Move)
        if not rsps:
            logger.warning("Failed to get next move from LLM")
            return None
        else:
            return rsps[0].move

    def play_puzzle(self, puzzle: ChessPuzzle):
        fen_string = puzzle.get_board_state()
        player = puzzle.get_current_player()
        previous_tries = []

        while len(previous_tries) < self.max_retries:
            next_move = self.get_next_move(fen_string, player, previous_tries)
            if next_move == None: #LLM not giving a output, should abort
                return False
            if puzzle.play_move(next_move): #Successfully played next move
                break
            else: #Illegal move, retry
                previous_tries.append(next_move)
        return len(previous_tries) < self.max_retries
            

class EngineGuidedLLMPlayer:
    def __init__(self):
        pass

class LanguageGuidedLLMPlayer:
    def __init__(self):
        pass