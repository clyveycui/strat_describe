from src.chess_puzzle import ChessPuzzle
from src.opponent import MainLineOpponent
from src.player import PureLLMPlayer

import pandas as pd
import argparse


def play_puzzle(puzzle, player, opponent):


def main():



if __name__ ==  '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--puzzles_file', type=str, default='./data/puzzles/lichess_db_puzzle.csv')
    args_parser.add_argument('--puzzle_id', type=str, default=None)
    args_parser.add_argument('--player_llm', type=str, default=)