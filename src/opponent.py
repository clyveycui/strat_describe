from src.engine import ChessEngine
from src.move_node import MoveNode
from src.tree_utils import minimax

# Exploits the enemy player by trying to foresee what the opponent will do.
class Opponent:
    #k: number of variations to explore.
    #d: number of steps to forsee. 1 means player plays 1 move. 2 means player plays 2 moves etc.
    def __init__(self, k, d, color:bool, engine: ChessEngine):
        self.k = k
        self.d = d
        self.engine = engine
        self.color = color
    
    #Returns the set of candidate moves
    def get_next_moves(self, fen_str, color):
        best_moves = self.engine.get_top_moves(fen=fen_str, k=self.k)
        best_moves_strings = [m['Move'] for m in best_moves]
        return best_moves_strings
    
    #Select the move that maximally exploit the opposing player
    def select_next_move(self, prev_node: MoveNode):
        assert prev_node.player == 1
        #assumes tree has been constructed
        next_node, score = minimax(prev_node, self.d*2, self.engine, player_color=not self.color)
        return next_node
    
    
        
    