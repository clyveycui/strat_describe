from src.move_node import MoveNode
from src.engine import ChessEngine
from numpy import argmin, argmax

def get_next_move_nodes(prev_node: MoveNode, player, opponent):
    #Player
    prev_player = prev_node.player
    next_fen = prev_node.next_fen
    next_color = not prev_node.color
    next_nodes = []
    if prev_player == 0:
        next_moves = player.get_next_moves(next_fen, next_color)
        assert next_moves != None
        for move in next_moves:
            next_nodes.append(MoveNode(player=1, board_fen=next_fen, move=move, color=next_color, parent=prev_node))
    elif prev_player == 1:
        next_moves = opponent.get_next_moves(next_fen, next_color)
        assert next_moves != None
        for move in next_moves:
            next_nodes.append(MoveNode(player=0, board_fen=next_fen, move=move, color=next_color, parent=prev_node))
    return next_nodes

#Assumes is constructed on the Opponent's turn
def construct_moves_tree(prev_node: MoveNode, player, opponent, remaining_moves: int):
    depth = opponent.d * 2
    depth = min(remaining_moves, depth)
    
    current_depth = 0
    current_frontier = [prev_node]
    next_frontier = []

    while current_depth < depth:
        for node in current_frontier:
            if node.has_children():
                next_frontier.extend(node.children)
            else:
                next_nodes = get_next_move_nodes(node, player, opponent)
                node.add_children(next_nodes)
                next_frontier.extend(next_nodes)
        current_depth += 1
        current_frontier = next_frontier
        next_frontier = []

#Gets score of node by performing minimax algorithm up to depth 
#Player is always maximizing, opponent always minimizing
def minimax(node: MoveNode, depth: int, engine: ChessEngine, white_is_max = True):
    if depth == 0 or not node.has_children():
        score = engine.eval_board(node.next_fen)
        if not white_is_max:
            score *= -1
        return None, score

    scores =[]
    for c in node.children:
        _, score = minimax(c, depth - 1, engine, white_is_max)
        scores.append(score)

    if node.next_player() == 0: 
        best_choice = argmin(scores)
    if node.next_player() == 1:
        best_choice = argmax(scores)
    
    score = scores[best_choice]
    next_node = node.children[best_choice]
    return next_node, score