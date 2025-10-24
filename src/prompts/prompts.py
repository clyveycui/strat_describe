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

#Does not keep track of previous messages
guided_LLM_stateless_get_next_move_prompt_structured_output = '''We are playing a game of Chess right now. You are given the current state of the board in FEN notation. You are also given a description of the strategy by a chess expert, which you should try to follow. You should come up with the next best move in the UCI format for the current player. 
{illegal_moves}
FEN:
{fen_str}
Current Player:
{player}
Strategy:
{strat_str}
Previous Sequence of Moves:
{prev_moves}

Please follow this JSON template:
{{
    "reason" : "<reasoning for the move>",
    "move" : "<chess move in UCI string>"
}}
'''

#Conversation styled:
guided_LLM_conversation_first_get_next_move_prompt_structured_output = '''We are playing a game of Chess right now. You are given the current state of the board in FEN notation. You are also given a description of the strategy by a chess expert, which you should try to follow. You should come up with the next best move in the UCI format for the current player. 
{illegal_moves}
FEN:
{fen_str}
Current Player:
{player}
Strategy:
{strat_str}

Please follow this JSON template:
{{
    "reason" : "<reasoning for the move>",
    "move" : "<chess move in UCI string>"
}}
'''


guided_LLM_conversation_next_get_next_move_prompt_structured_output = '''Here is the opponent's move in UCI format and the current state of the board in FEN notation. Remember to try to follow the strategy by the chess expert. You should come up with the next best move in the UCI format for the current player. 
{illegal_moves}
Opponent's move:
{opp_move}
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

guided_LLM_conversation_next_reminded_get_next_move_prompt_structured_output = '''Here is the opponent's move in UCI format and the current state of the board in FEN notation. Remember to try to follow the strategy by the chess expert. You should come up with the next best move in the UCI format for the current player. 
{illegal_moves}
Opponent's move:
{opp_move}
FEN:
{fen_str}
Current Player:
{player}
Strategy:
{strat_str}

Please follow this JSON template:
{{
    "reason" : "<reasoning for the move>",
    "move" : "<chess move in UCI string>"
}}
'''

verbalize_main_line_structured_output = '''We are playing a game of Chess right now. You are given the current state of the board in FEN notation and the principle line in UCI format as calculated by a chess engine. You should provide a high level description of this line of moves from the perspective of the current player and the possible responses by the opponent so that another chess player will be able to follow this description and play the strategy as shown here. Keep it short and sweet.

FEN:
{fen_str}
Current Player:
{player}
Principle Line:
{principle_line}

Please follow this JSON template:
{{
"description" : "<description of the principle line and the strategy behind it>",
}}
'''

verbalize_main_line_structured_output = '''We are playing a game of Chess right now. You are given the current state of the board in FEN notation and the principle line in UCI format as calculated by a chess engine. You should provide a high level description of this line of moves and the possible responses by the opponent so that another chess player will be able to follow this description and play the strategy as shown here. Keep it short and sweet.

FEN:
{fen_str}
Current Player:
{player}
Principle Line:
{principle_line}
'''