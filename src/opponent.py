from src.engine import ChessEngine
from src.move_node import MoveNode
from src.tree_utils import minimax

# Exploits the enemy player by trying to foresee what the opponent will do.
class Opponent:
    #k: number of variations to explore.
    #d: number of steps to forsee. 1 means player plays 1 move. 2 means player plays 2 moves etc.
    def __init__(self, k, d, engine: ChessEngine):
        self.k = k
        self.d = d
        self.engine = engine
    
    #Returns the set of candidate moves
    def get_next_moves(self, fen_str, color):
        best_moves = self.engine.get_top_moves(fen=fen_str, k=self.k)
        return best_moves
    
    #Select the move that maximally exploit the opposing player
    def select_next_move(self, curr_node: MoveNode):
        assert curr_node.player == 0
        #assumes tree has been constructed
        next_node, score = minimax(curr_node, self.d*2)
        return next_node
    
    
        
    