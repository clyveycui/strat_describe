class ChessPuzzle:
    def __init__(self, fen, main_line):
        self.fen = fen
        self.initial_move_uci = main_line[0]
        self.solution = main_line
        fen_player = fen.split()[1]
        self.solving_player = fen_player != 'w'#True for white, False for black
        self.moves_to_play = len(main_line) - 1

    
    def is_complete(self):
        return self.current_moves == self.moves_to_play
    
    def get_board_state(self):
        return self.board.fen()

    def get_current_player(self):
        return self.board.turn