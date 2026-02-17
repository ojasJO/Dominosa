import numpy as np
from collections import defaultdict
from structures import CellNode, EdgeBond, BondState


class DominosaBoard:
    __slots__ = ("rows", "cols", "grid", "cells", "edges", "possible_moves")

    def __init__(self, matrix: np.ndarray):
        self.rows, self.cols = matrix.shape
        self.grid = matrix
        self.cells = self._init_cells()
        self.edges = []
        self.possible_moves = defaultdict(list)

        self._init_graph_connections()
        self._init_constraints()

    def _init_cells(self):
        grid = self.grid
        return [[CellNode(r, c, grid[r, c])
                 for c in range(self.cols)]
                 for r in range(self.rows)]

    def _init_graph_connections(self):
        cells = self.cells
        edges = self.edges
        create = self._create_bond

        for r in range(self.rows):
            row = cells[r]
            for c in range(self.cols - 1):
                create(row[c], row[c + 1])

        for r in range(self.rows - 1):
            row = cells[r]
            next_row = cells[r + 1]
            for c in range(self.cols):
                create(row[c], next_row[c])

    def _create_bond(self, node_a, node_b):
        bond = EdgeBond(node_a, node_b)
        self.edges.append(bond)
        node_a.neighbors.append(node_b)
        node_b.neighbors.append(node_a)

    def _init_constraints(self):
        pm = self.possible_moves
        for edge in self.edges:
            pm[edge.get_pair_id()].append(edge)

    def get_cell(self, r, c):
        return self.cells[r][c]
