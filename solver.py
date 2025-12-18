from structures import BondState
from board import DominosaBoard


class Solver:
    def __init__(self, board: DominosaBoard):
        self.board = board
        self.log = []

    def step(self):
        move = self._find_unique_move()
        if move:
            self._apply_move(move, "Uniqueness (Global)")
            return True

        move = self._find_isolated_move()
        if move:
            self._apply_move(move, "Isolation (Local)")
            return True

        return False

    def _apply_move(self, edge, reason):
        edge.state = BondState.CONFIRMED
        edge.node_a.occupied = True
        edge.node_b.occupied = True

        pair = edge.get_pair_id()
        msg = f"Placed {pair} at {edge.node_a.r},{edge.node_a.c} | Reason: {reason}"
        print(msg)
        self.log.append(msg)

        self._block_neighbors(edge.node_a)
        self._block_neighbors(edge.node_b)

        if pair in self.board.possible_moves:
            del self.board.possible_moves[pair]

        self._clean_invalid_possibilities()

    def _block_neighbors(self, node):
        for edge in self.board.edges:
            if edge.state == BondState.UNDECIDED:
                if edge.node_a == node or edge.node_b == node:
                    edge.state = BondState.BLOCKED

    def _clean_invalid_possibilities(self):
        for pair_id in list(self.board.possible_moves.keys()):
            self.board.possible_moves[pair_id] = [
                e for e in self.board.possible_moves[pair_id]
                if e.state == BondState.UNDECIDED
            ]

    def _find_unique_move(self):
        for _, edge_list in self.board.possible_moves.items():
            if len(edge_list) == 1:
                return edge_list[0]
        return None

    def _find_isolated_move(self):
        for row in self.board.cells:
            for cell in row:
                if cell.occupied:
                    continue

                valid_bonds = []
                for edge in self.board.edges:
                    if edge.state == BondState.UNDECIDED:
                        if edge.node_a == cell or edge.node_b == cell:
                            valid_bonds.append(edge)

                if len(valid_bonds) == 1:
                    return valid_bonds[0]
        return None
