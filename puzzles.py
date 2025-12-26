import numpy as np
import random

class PuzzleDB:

    BOARDS_3 = [
        np.array([
            [0, 1, 1, 2, 2],
            [0, 3, 3, 0, 1],
            [2, 3, 0, 2, 3],
            [1, 1, 2, 3, 0]
        ])
    ]


    BOARDS_4 = [
        np.array([
            [0, 1, 1, 2, 2, 3],
            [0, 4, 4, 3, 3, 0],
            [1, 4, 2, 0, 1, 4],
            [2, 3, 0, 4, 1, 2],
            [3, 2, 3, 1, 0, 4]
        ])
    ]


    BOARDS_5 = [
        np.array([
            [0, 1, 1, 2, 2, 3, 3],
            [0, 4, 4, 5, 5, 0, 1],
            [2, 3, 4, 1, 0, 2, 5],
            [3, 5, 2, 0, 4, 1, 3],
            [4, 2, 5, 3, 1, 0, 4],
            [5, 1, 0, 4, 2, 3, 5]
        ])
    ]


    BOARDS_6 = [
        np.array([
            [0, 1, 1, 2, 2, 3, 3, 4],
            [0, 5, 5, 4, 4, 6, 6, 0],
            [1, 5, 2, 3, 6, 0, 1, 2],
            [3, 4, 5, 6, 1, 2, 3, 4],
            [6, 2, 3, 0, 4, 5, 1, 6],
            [5, 3, 0, 1, 2, 6, 4, 5],
            [6, 4, 1, 2, 3, 0, 5, 6]
        ])
    ]


    BOARDS_9 = []


    @staticmethod
    def get_board(n):

        options = []
        
        if n == 3: options = PuzzleDB.BOARDS_3
        elif n == 4: options = PuzzleDB.BOARDS_4
        elif n == 5: options = PuzzleDB.BOARDS_5
        elif n == 6: options = PuzzleDB.BOARDS_6
        elif n == 9: options = PuzzleDB.BOARDS_6 

        if not options:
            return PuzzleDB.BOARDS_3[0]
            
        return random.choice(options)
