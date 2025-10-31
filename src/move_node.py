from src.chess_utils import get_next_fen, bool_to_color_str

class MoveNode:
    def __init__(self, player, board_fen, move, color, parent=None):
        self.parent = parent
        self.children = []
        self.player = player # 1 for player, 0 for opponent
        self.color = color # True for White, False for black
        self.board_fen = board_fen
        self.move = move
        self.next_fen = get_next_fen(self.board_fen, self.move)


    def has_children(self):
        return len(self.children) > 0
    
    def add_children(self, nodes):
        self.children.extend(nodes)

    def next_player(self):
        return (self.player + 1) % 2
    
    def color_string(self):
        return bool_to_color_str(self.color)
    
    def next_color(self):
        return not self.color
        
    def __repr__(self):
        return self.move
                
