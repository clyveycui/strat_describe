import chess

class ChessPuzzle:
    def __init__(self, fen, main_line):
        self.fen = fen
        self.initial_move_uci = main_line[0]
        self.solution = main_line
        self.solving_player = self.board.turn#True for white, False for black
        self.moves_to_play = len(main_line)
        self.current_moves = 1

    def play_move(self, move_uci):
        move = chess.Move.from_uci(move_uci)
        if not self.board.is_legal(move=move):
            return False
        self.board.push(move)
        self.current_moves += 1
        return True
    
    def is_complete(self):
        return self.current_moves == self.moves_to_play
    
    def get_board_state(self):
        return self.board.fen()

    def get_current_player(self):
        return self.board.turn
    
    def get_remaining_moves(self):
        return self.moves_to_play - self.current_moves