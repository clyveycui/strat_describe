from stockfish import Stockfish

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
            return 100000 if eval['value'] > 1 else -100000
        
    def get_top_moves(self, fen, k):
        self.stockfish.set_fen_position(fen)
        return self.stockfish.get_top_moves(k)