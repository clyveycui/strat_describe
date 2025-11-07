from stockfish import Stockfish
from src.chess_utils import get_color_from_fen, CHECK_MATE_SCORE
from src.move_node import MoveNode

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
                curr_p = get_color_from_fen(fen)
                return CHECK_MATE_SCORE if not curr_p else -CHECK_MATE_SCORE
            return CHECK_MATE_SCORE if eval['value'] >= 1 else -CHECK_MATE_SCORE
        
    def get_top_moves(self, fen, k):
        self.stockfish.set_fen_position(fen)
        return self.stockfish.get_top_moves(k)
    
    #j : opponent variations to consider
    #c : number of moves to play in total, should be odd
    def get_strategy(self, fen:str, j:int, c:int):
        #using move node to construct a quick and simple strategy
        def iter(cc:int, prev_node:MoveNode, move:str, player:bool):
            if prev_node == None:
                cur_node = MoveNode(1 if player else 0, fen, move, get_color_from_fen(fen), prev_node)
            else:
                cur_node = MoveNode(prev_node.next_player(), prev_node.next_fen, move, prev_node.next_color(), prev_node)
            if cc == c:
                assert player
                return cur_node
            
            next_moves = self.get_top_moves(cur_node.next_fen, j if player else 1)
            next_nodes = [iter(cc + 1, cur_node, m['Move'], not player) for m in next_moves]
            cur_node.add_children(next_nodes)
            return cur_node
        
        best_move = self.get_top_moves(fen, 1)[0]['Move']
        
        root = iter(1, None, best_move, True)
        return root