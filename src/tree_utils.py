from src.move_node import MoveNode
from src.engine import ChessEngine
from src.chess_utils import CHECK_MATE_SCORE
from numpy import argmin, argmax, abs
from json import dumps


def get_next_move_nodes(prev_node: MoveNode, player, opponent):
    #Player
    prev_player = prev_node.player
    next_fen = prev_node.next_fen
    next_color = not prev_node.color
    next_nodes = []
    if prev_player == 0:
        next_moves = player.get_next_moves(prev_node)
        assert next_moves != None
        for move in next_moves:
            next_nodes.append(MoveNode(player=1, board_fen=next_fen, move=move, color=next_color, parent=prev_node))
    elif prev_player == 1:
        next_moves = opponent.get_next_moves(prev_node)
        assert next_moves != None
        for move in next_moves:
            next_nodes.append(MoveNode(player=0, board_fen=next_fen, move=move, color=next_color, parent=prev_node))
    return next_nodes

#Assumes is constructed on the Opponent's turn
#We can prune by just halting the moment we see a bad move by the LLM player, since opponent chooses which branch to go
def construct_moves_tree(prev_node: MoveNode, player, opponent, engine, remaining_moves: int, ref_score: int, prune_val: int = 2 * CHECK_MATE_SCORE):
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
                if prune_val < 2 * CHECK_MATE_SCORE and node.player == 0:
                    assert len(next_nodes) == 1
                    node = next_nodes[0]
                    if should_prune(node, prune_val, engine, ref_score):
                        return node
                next_frontier.extend(next_nodes)
        current_depth += 1
        current_frontier = next_frontier
        next_frontier = []
    return None
#Gets score of node by performing minimax algorithm up to depth 
#Player is always maximizing, opponent always minimizing
def minimax(node: MoveNode, depth: int, engine: ChessEngine, player_color: bool):
    if depth == 0 or not node.has_children():
        score = engine.eval_board(node.next_fen)
        if not player_color:
            score *= -1
        return None, score

    scores =[]
    for c in node.children:
        _, score = minimax(c, depth - 1, engine, player_color)
        scores.append(score)

    if node.next_player() == 0: 
        best_choice = argmin(scores)
    if node.next_player() == 1:
        best_choice = argmax(scores)
    
    score = scores[best_choice]
    next_node = node.children[best_choice]
    return next_node, score

def get_sequence_of_moves(node: MoveNode, algebraic: bool=True):
    if algebraic:
        move = node.move_algebraic
    else:
        move = node.move
    if node.parent == None:
        return [move]
    previous_moves = get_sequence_of_moves(node.parent, algebraic)
    previous_moves.append(move)
    return previous_moves

def get_json(node: MoveNode):
    def recurse(node):    
        return {'player' : node.color_string(), 'move' : node.move_algebraic, 'responses' : [recurse(c) for c in node.children] if node.has_children() else []}
    return dumps(recurse(node), indent=2)

def should_prune(node: MoveNode, prune_val, engine, ref_score):
    next_score = engine.eval_board(node.next_fen)
    score_decrease = ref_score - next_score if node.color else next_score - ref_score
    if score_decrease > prune_val:
        return True
    return False
