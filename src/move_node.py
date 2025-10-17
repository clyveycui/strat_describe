from src.chess_utils import get_next_fen

class MoveNode:
    def __init__(self, player, board_fen, move, color, parent=None):
        self.parent = parent
        self.children = []
        self.player = player # 1 for player, 0 for opponent
        self.color = color # True for White, False for black
        self.board_fen = board_fen
        self.next_fen = get_next_fen(self.board_fen, self.move)
        self.move = move

    def has_children(self):
        return len(self.children) > 0
    
    def add_children(self, nodes):
        self.children.extend(nodes)

    def next_player(self):
        return (self.player + 1) % 2

        
    
                
