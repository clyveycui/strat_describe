from src.llm.llm import LanguageModel

class LLMVerbalizer:
    def __init__(self, llm : LanguageModel, max_retries : int = 3, conversational : bool=False):
        self.llm = llm
        self.max_retries = max_retries

    #Takes in a list of moves, verbalizes it to the 
    def verbalize_main_line(self, main_line: list):
        pass