from typing import List, Tuple, Set
from structures import CellNode, EdgeBond, BondState


class DominosaBoard:
    def __init__(self, matrix: List[List[int]]):
        # Basic grid dimensions
        self.rows = len(matrix)
        self.cols = len(matrix[0])
        self.matrix_data = matrix

        # Initialize cells (graph nodes)
        self.cells: List[List[CellNode]] = [
            [CellNode(r, c, val) for c, val in enumerate(row)]
            for r, row in enumerate(matrix)
        ]

      
        self.edges: List[EdgeBond] = []

       
        self.available_dominoes: Set[Tuple[int, int]] = set()
        self.placed_dominoes: Set[Tuple[int, int]] = set()

       
        self._init_topology()
        self._init_domino_set()
        self.total_dominoes = len(self.available_dominoes)

    # TOPOLOGY
 
    def _init_topology(self):
       # horizontal and vertical connctions to ensure each adjacent pair has only one EdgeBond
        for r in range(self.rows):
            for c in range(self.cols):
                current = self.cells[r][c]
                if c + 1 < self.cols:
                    self._create_bond(current, self.cells[r][c + 1])
                if r + 1 < self.rows:
                    self._create_bond(current, self.cells[r + 1][c])

    def _create_bond(self, node_a: CellNode, node_b: CellNode):
        
        # creates EdgeBond and links both directions.
        

        bond = EdgeBond(node_a, node_b)
        self.edges.append(bond)

        # linkn edge to node 
        node_a.edges.append(bond)
        node_b.edges.append(bond)

        # neighbour tracking
        node_a.neighbors.append(node_b)
        node_b.neighbors.append(node_a)

        #  [POTENTIAL BUG]
        # If structures.CellNode does not initialize:
        #   self.edges = []
        #   self.neighbors = []
        # this will raise AttributeError.


# domino set initialization
    def _init_domino_set(self):
        """
        Generate all possible domino pairs (i, j)
        where 0 <= i <= j <= max_value.
        """

        if not self.cells:
            return

        max_val = max(
            max(cell.value for cell in row)
            for row in self.cells
        )

        self.available_dominoes = {
            (i, j)
            for i in range(max_val + 1)
            for j in range(i, max_val + 1)
        }

        # [INCOMPLETE]
        # This assumes a FULL domino set from 0 to max_val.
        # If your puzzle is supposed to use a restricted set,
        # this must be replaced with puzzle-specific input.



    # EDGE LOOKUP


    def get_edge(self, n1: CellNode, n2: CellNode):
        """
        Returns the EdgeBond between two nodes.
        O(degree) lookup.
        """

        for e in n1.edges:
            if (
                (e.node_a == n1 and e.node_b == n2) or
                (e.node_a == n2 and e.node_b == n1)
            ):
                return e

        return None

        # ⚠️ [POTENTIAL OPTIMIZATION]
        # This is linear search. For large boards,
        # a hash map of (node_id, node_id) -> edge would be faster.


    # --------------------------------------------------
    # MOVE VALIDATION
    # --------------------------------------------------

    def validate_move(self, node_a: CellNode, node_b: CellNode) -> bool:
        """
        Pre-check if a move is legal.
        Does NOT modify state.
        """

        # Must be neighbors
        if node_b not in node_a.neighbors:
            return False

        # Cells must be free
        if node_a.occupied or node_b.occupied:
            return False

        # Domino must still be available
        pair = tuple(sorted((node_a.value, node_b.value)))
        if pair not in self.available_dominoes:
            return False

        return True



    # PLACEMENT LOGIC


    def confirm_edge(self, edge: EdgeBond, owner_id: int = 1) -> bool:
        """
        Place a domino permanently.
        """

        if edge.state == BondState.BLOCKED:
            return False

        pair = edge.get_pair_id()

        if pair not in self.available_dominoes:
            return False

        # Commit edge state
        edge.state = BondState.CONFIRMED
        edge.owner_id = owner_id

        # Occupy cells
        edge.node_a.occupied = True
        edge.node_b.occupied = True
        edge.node_a.owner_id = owner_id
        edge.node_b.owner_id = owner_id

        # Update domino sets
        self.available_dominoes.remove(pair)
        self.placed_dominoes.add(pair)

        self._update_blocked_states()

        return True


        # No rollback safety. If an exception occurs mid-function,
        # board state could be inconsistent.



    # REMOVAL LOGIC (UNDO)


    def remove_edge(self, edge: EdgeBond):
        """
        Undo a previously placed domino.
        """

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

        #  [POTENTIAL BUG]
        # Assumes pair exists in placed_dominoes.
        # If called incorrectly, could raise KeyError.


    # --------------------------------------------------
    # BLOCKED EDGE RECOMPUTATION
    # --------------------------------------------------

    def _update_blocked_states(self):
        """
        Recalculate all non-confirmed edges.
        """

        # Reset non-confirmed edges
        for e in self.edges:
            if e.state != BondState.CONFIRMED:
                e.state = BondState.UNDECIDED

        # Mark edges blocked if touching occupied cell
        for e in self.edges:
            if e.state == BondState.UNDECIDED:
                if e.node_a.occupied or e.node_b.occupied:
                    e.state = BondState.BLOCKED

        #  [INCOMPLETE]
        # This only blocks due to occupancy.
        # It does NOT block edges due to domino exhaustion
        # (i.e., pair no longer available).
        # That could be added for stronger constraint propagation.


    # --------------------------------------------------
    # GAME STATE CHECK
    # --------------------------------------------------

    def has_valid_moves(self) -> bool:
        """
        Returns True if at least one legal placement exists.
        """

        for edge in self.edges:
            if (
                edge.state == BondState.UNDECIDED and
                not edge.node_a.occupied and
                not edge.node_b.occupied and
                edge.get_pair_id() in self.available_dominoes
            ):
                return True

        return False


    # --------------------------------------------------
    # PROGRESS TRACKING
    # --------------------------------------------------

    def get_progress(self) -> float:
        """
        Returns ratio of placed dominoes to total.
        """

        if self.total_dominoes == 0:
            return 0.0

        return len(self.placed_dominoes) / self.total_dominoes
