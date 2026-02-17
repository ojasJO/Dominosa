import numpy as np
import random


class PuzzleDB:

    BOARDS = {
        3: [
            np.array([
                [0, 1, 1, 2, 2],
                [0, 3, 3, 0, 1],
                [2, 3, 0, 2, 3],
                [1, 1, 2, 3, 0]
            ])
        ],

        4: [
            np.array([
                [0, 1, 1, 2, 2, 3],
                [0, 4, 4, 3, 3, 0],
                [1, 4, 2, 0, 1, 4],
                [2, 3, 0, 4, 1, 2],
                [3, 2, 3, 1, 0, 4]
            ])
        ],

        5: [
            np.array([
                [0, 1, 1, 2, 2, 3, 3],
                [0, 4, 4, 5, 5, 0, 1],
                [2, 3, 4, 1, 0, 2, 5],
                [3, 5, 2, 0, 4, 1, 3],
                [4, 2, 5, 3, 1, 0, 4],
                [5, 1, 0, 4, 2, 3, 5]
            ])
        ],

        6: [
            np.array([
                [0, 1, 1, 2, 2, 3, 3, 4],
                [0, 5, 5, 4, 4, 6, 6, 0],
                [1, 5, 2, 3, 6, 0, 1, 2],
                [3, 4, 5, 6, 1, 2, 3, 4],
                [6, 2, 3, 0, 4, 5, 1, 6],
                [5, 3, 0, 1, 2, 6, 4, 5],
                [6, 4, 1, 2, 3, 0, 5, 6]
            ])
        ],

        9: [] 
    }

    DEFAULT_SIZE = 3

    @staticmethod
    def get_board(n: int) -> np.ndarray:
        boards = PuzzleDB.BOARDS.get(n) or PuzzleDB.BOARDS[PuzzleDB.DEFAULT_SIZE]
        return random.choice(boards).copy()
