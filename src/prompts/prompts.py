pure_LLM_get_next_move_prompt_structured_output = '''We are playing a game of Chess right now. You are given the current state of the board in FEN notation. You should come up with the next best move in the UCI format for the current player. 
{illegal_moves}
FEN:
{fen_str}
Current Player:
{player}

Please follow this JSON template:
{{
    "reason" : "<reasoning for the move>",
    "move" : "<chess move in UCI string>"
}}
'''

illegal_moves_str = '''The following moves are illegal and cannot be made by the current player:
{illegal_moves}.'''