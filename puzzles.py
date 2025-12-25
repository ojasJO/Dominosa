import numpy as np
import random

class PuzzleDB:

    BOARDS_3 = [
        np.array([
            [0, 0, 1, 1, 2],
            [3, 3, 2, 2, 0],
            [1, 3, 0, 2, 3],
            [1, 2, 3, 1, 0]
        ])
    ]


    BOARDS_4 = [
        np.array([
            [0, 0, 1, 1, 2, 2],
            [3, 3, 4, 4, 0, 1],
            [2, 3, 4, 1, 0, 3],
            [2, 4, 1, 0, 2, 4],
            [3, 1, 0, 3, 4, 2]
        ])
    ]

    BOARDS_5 = [
        np.array([
            [0, 0, 1, 1, 2, 2, 3],
            [3, 4, 4, 5, 5, 0, 1],
            [2, 3, 4, 5, 0, 1, 2],
            [5, 1, 3, 0, 2, 4, 5],
            [3, 4, 1, 2, 0, 5, 4],
            [3, 5, 0, 2, 1, 4, 3]
        ])
    ]


    BOARDS_6 = [
        np.array([
            [0, 0, 1, 1, 2, 2, 3, 3],
            [4, 4, 5, 5, 6, 6, 0, 1],
            [2, 3, 4, 5, 6, 0, 1, 2],
            [3, 4, 5, 6, 0, 1, 2, 3],
            [6, 1, 2, 3, 4, 5, 0, 4],
            [5, 2, 0, 1, 3, 6, 5, 4],
            [6, 3, 1, 2, 4, 0, 5, 6]
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