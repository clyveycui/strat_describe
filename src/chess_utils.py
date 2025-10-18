import chess

def validate_move(fen, move_uci):
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    return board.is_legal(move)

def get_next_fen(fen, move_uci):
    board = chess.Board(fen)
    board.push_uci(move_uci)
    return board.fen()

#True for white, False for black
def get_player_from_fen(fen):
    return fen.split()[1] == 'w'