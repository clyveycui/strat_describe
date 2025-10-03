from src.chess_puzzle import ChessPuzzle

class MainLineOpponent:    
    def play_puzzle(self, puzzle: ChessPuzzle):
        next_move = puzzle.get_next_main_line_move()
        return puzzle.play_move(next_move)
        