import numpy as np
from structures import CellNode, EdgeBond, BondState


class DominosaBoard:
    def __init__(self, matrix: np.ndarray):
        self.rows, self.cols = matrix.shape
        self.grid = matrix
        self.cells = [
            [CellNode(r, c, matrix[r, c]) for c in range(self.cols)]
            for r in range(self.rows)
        ]
        self.edges = []
        self.possible_moves = {}
        self._init_graph_connections()
        self._init_constraints()

    def _init_graph_connections(self):
        for r in range(self.rows):
            for c in range(self.cols - 1):
                a = self.cells[r][c]
                b = self.cells[r][c + 1]
                bond = EdgeBond(a, b)
                self.edges.append(bond)
                a.neighbors.append(b)
                b.neighbors.append(a)

        for r in range(self.rows - 1):
            for c in range(self.cols):
                a = self.cells[r][c]
                b = self.cells[r + 1][c]
                bond = EdgeBond(a, b)
                self.edges.append(bond)
                a.neighbors.append(b)
                b.neighbors.append(a)

    def _init_constraints(self):
        for edge in self.edges:
            pid = edge.get_pair_id()
            self.possible_moves.setdefault(pid, []).append(edge)

    def get_cell(self, r, c):
        return self.cells[r][c]
