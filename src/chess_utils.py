import chess

CHECK_MATE_SCORE = 100000

def validate_move(fen, move_uci):
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    return board.is_legal(move)

def get_next_fen(fen, move_uci):
    board = chess.Board(fen)
    board.push_uci(move_uci)
    return board.fen()

#True for white, False for black
def get_color_from_fen(fen):
    return fen.split()[1] == 'w'

def bool_to_color_str(color_bool):
    return 'White' if color_bool else 'Black'

def uci_to_algebraic(fen, uci):
    assert validate_move(fen, uci)
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(uci)
        algebraic = board.san(move)
        return algebraic
    except chess.InvalidMoveError:
        return None

def algebraic_to_uci(fen, algebraic):
    try:
        board = chess.Board(fen)
        move = board.parse_san(algebraic)
        return move.uci()
    except chess.IllegalMoveError:
        return None
