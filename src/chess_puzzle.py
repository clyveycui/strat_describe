import chess

class ChessPuzzle:
    def __init__(self, fen, main_line):
        self.fen = fen
        self.board = chess.Board(fen)
        self.main_line_uci = main_line
        self.initial_move_uci = main_line[0]
        self.board.push_uci(self.initial_move_uci)
        self.solving_player = self.board.turn#True for white, False for black
        self.moves_to_play = len(self.main_line)
        self.current_moves = 1

    def play_move(self, move):
        move = chess.Move.from_uci(move)
        if not self.board.is_legal(move=move):
            return False
        self.board.push_uci(move)
        self.current_moves += 1
        return True

    def get_next_main_line_move(self):
        return self.main_line_uci[self.current_moves]
    
    def get_board_state(self):
        return self.board.fen

    def get_current_player(self):
        return self.board.turn