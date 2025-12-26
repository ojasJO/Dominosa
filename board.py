import numpy as np
from structures import CellNode, EdgeBond, BondState

class DominosaBoard:
    def __init__(self, matrix: np.ndarray):
        self.rows, self.cols = matrix.shape
        self.grid = matrix
        self.cells = []
        self.edges = []
        self.possible_moves = {}

        self._init_cells()
        self._init_graph_connections()
        self._init_constraints()

    def _init_cells(self):
        for r in range(self.rows):
            row_cells = []
            for c in range(self.cols):
                row_cells.append(CellNode(r, c, self.grid[r, c]))
            self.cells.append(row_cells)

    def _init_graph_connections(self):
        for r in range(self.rows):
            for c in range(self.cols - 1):
                self._create_bond(self.cells[r][c], self.cells[r][c + 1])

        for r in range(self.rows - 1):
            for c in range(self.cols):
                self._create_bond(self.cells[r][c], self.cells[r + 1][c])

    def _create_bond(self, node_a, node_b):
        bond = EdgeBond(node_a, node_b)
        self.edges.append(bond)
        node_a.neighbors.append(node_b)
        node_b.neighbors.append(node_a)

    def _init_constraints(self):
        for edge in self.edges:
            pid = edge.get_pair_id()
            if pid not in self.possible_moves:
                self.possible_moves[pid] = []
            self.possible_moves[pid].append(edge)

    def get_cell(self, r, c):
        return self.cells[r][c]
