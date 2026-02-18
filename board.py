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

    # to return edge opject between two vertices
    def get_edge(self, n1: CellNode, n2: CellNode):
    for e in n1.edges:
        if (e.node_a == n1 and e.node_b == n2) or \
           (e.node_a == n2 and e.node_b == n1):
            return e
    return None


    # validator 
    def validate_move(self, node_a: CellNode, node_b: CellNode) -> bool:
    
    if node_b not in node_a.neighbors:
        return False

    if node_a.occupied or node_b.occupied:
        return False

    pair = tuple(sorted((node_a.value, node_b.value)))

    if pair not in self.available_dominoes:
        return False

    return True

    # placement logic 
    def confirm_edge(self, edge: EdgeBond, owner_id: int = 1) -> bool:
    """Place a domino."""
    if edge.state == BondState.BLOCKED:
        return False

    pair = edge.get_pair_id()

    if pair not in self.available_dominoes:
        return False

    # Commit state
    edge.state = BondState.CONFIRMED
    edge.owner_id = owner_id

    edge.node_a.occupied = True
    edge.node_b.occupied = True
    edge.node_a.owner_id = owner_id
    edge.node_b.owner_id = owner_id

    self.available_dominoes.remove(pair)
    self.placed_dominoes.add(pair)

    self._update_blocked_states()
    return True

    # removal logic 

    def remove_edge(self, edge: EdgeBond):
    """Undo a placed domino."""
    if edge.state != BondState.CONFIRMED:
        return

    pair = edge.get_pair_id()

    edge.state = BondState.UNDECIDED
    edge.owner_id = 0

    edge.node_a.occupied = False
    edge.node_b.occupied = False
    edge.node_a.owner_id = 0
    edge.node_b.owner_id = 0

    self.placed_dominoes.remove(pair)
    self.available_dominoes.add(pair)

    self._update_blocked_states()

    # blocked state recaulcualtion 

    def _update_blocked_states(self):
    """Recalculate blocked edges."""
    for e in self.edges:
        if e.state != BondState.CONFIRMED:
            e.state = BondState.UNDECIDED

    for e in self.edges:
        if e.state == BondState.UNDECIDED:
            if e.node_a.occupied or e.node_b.occupied:
                e.state = BondState.BLOCKED
# game over check valididty 
    def has_valid_moves(self) -> bool:
    for edge in self.edges:
        if (edge.state == BondState.UNDECIDED and
            not edge.node_a.occupied and
            not edge.node_b.occupied and
            edge.get_pair_id() in self.available_dominoes):
            return True
    return False




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
