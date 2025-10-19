from stockfish import Stockfish
from src.chess_utils import get_player_from_fen

class ChessEngine:
    
    def __init__(self, stockfish_bins=None):
        if stockfish_bins != None:
            self.stockfish = Stockfish(stockfish_bins)
        else:
            self.stockfish = Stockfish()  
    
    def eval_board(self, fen):
        self.stockfish.set_fen_position(fen)
        eval = self.stockfish.get_evaluation()
        if eval['type'] == 'cp':
            return eval['value']
        elif eval['type'] == 'mate':
            # If value == 0 then last moved player wins
            if eval['value']== 0:
                curr_p = get_player_from_fen(fen)
                return 100000 if not curr_p else -100000
            return 100000 if eval['value'] >= 1 else -100000
        
    def get_top_moves(self, fen, k):
        self.stockfish.set_fen_position(fen)
        return self.stockfish.get_top_moves(k)