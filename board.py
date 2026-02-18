from structures import CellNode, EdgeBond, BondState
from typing import List, Tuple, Set

class DominosaBoard:
    def __init__(self, matrix: List[List[int]]):
        # numpy shape logic completely changed
        self.rows = len(matrix)
        self.cols = len(matrix[0])
        self.matrix_data = matrix

        # glid initilaized proeprly (preiviious one used to bug when algorithm was chnaged midgame)  
        self.cells = [
            [CellNode(r, c, val) for c, val in enumerate(row)]
            for r, row in enumerate(matrix)
        ]

        self.edges: List[EdgeBond] = []

        # NEW -> domino tracking system introduced 
        
        self.available_dominoes: Set[Tuple[int, int]] = set()
        self.placed_dominoes: Set[Tuple[int, int]] = set()

        self._init_topology()
        self._init_domino_set()

        self.total_dominoes = len(self.available_dominoes)

    def _init_topology(self):
        
        for r in range(self.rows):
            for c in range(self.cols):
                curr = self.cells[r][c]

                if c + 1 < self.cols:
                    self._create_bond(curr, self.cells[r][c + 1])

                if r + 1 < self.rows:
                    self._create_bond(curr, self.cells[r + 1][c])

    def _create_bond(self, node_a, node_b):
        bond = EdgeBond(node_a, node_b)
        self.edges.append(bond)

        # Keep neighbor tracking
        node_a.neighbors.append(node_b)
        node_b.neighbors.append(node_a)

    def _init_domino_set(self):

        if not self.cells:
            return

        max_val = max(max(cell.value for cell in row) for row in self.cells)

        self.available_dominoes = {
            (i, j)
            for i in range(max_val + 1)
            for j in range(i, max_val + 1)
        }

    def get_cell(self, r, c):
        return self.cells[r][c]
