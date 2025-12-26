from structures import BondState, StrategyLevel
from board import DominosaBoard

class Solver:
    def _init_(self, board: DominosaBoard):
        self.board = board

    def rebuild_constraints(self):
        self.board.possible_moves.clear()
        
        for edge in self.board.edges:
            if edge.state == BondState.BLOCKED:
                edge.state = BondState.UNDECIDED
            
            pid = edge.get_pair_id()
            if pid not in self.board.possible_moves:
                self.board.possible_moves[pid] = []
            self.board.possible_moves[pid].append(edge)

        confirmed_edges = [e for e in self.board.edges if e.state == BondState.CONFIRMED]
        
        for edge in confirmed_edges:
            pair = edge.get_pair_id()
            if pair in self.board.possible_moves:
                del self.board.possible_moves[pair]
            
            self._block_neighbors(edge.node_a)
            self._block_neighbors(edge.node_b)
            
        self._clean_invalid_possibilities()

    def sanity_check(self):
        placed_pairs = []
        for edge in self.board.edges:
            if edge.state == BondState.CONFIRMED:
                pair = edge.get_pair_id()
                if pair in placed_pairs:
                    return f"ERROR: Duplicate Pair {pair} found!"
                placed_pairs.append(pair)
        return None

    def find_hint(self, strategy: StrategyLevel):
        error = self.sanity_check()
        if error: return None, error

        if strategy == StrategyLevel.LEVEL_3_ADVANCED:
            move = self._find_duplicate_blocker()
            if move: return move, "Duplicate Prevention (Wall)"

        move = self._find_unique_move()
        if move: return move, "Uniqueness (Global)"

        if strategy != StrategyLevel.LEVEL_1_BASIC:
            move = self._find_isolated_move()
            if move: return move, "Isolation (Local)"

        return None, "No forced moves found."

    def apply_move(self, edge):
        if edge.state == BondState.BLOCKED: return 
            
        edge.state = BondState.CONFIRMED
        edge.node_a.occupied = True
        edge.node_b.occupied = True
        
        self._block_neighbors(edge.node_a)
        self._block_neighbors(edge.node_b)

        pair = edge.get_pair_id()
        if pair in self.board.possible_moves:
            del self.board.possible_moves[pair]
            
        self._clean_invalid_possibilities()

    def _find_duplicate_blocker(self):
        placed_pairs = set()
        for edge in self.board.edges:
            if edge.state == BondState.CONFIRMED:
                placed_pairs.add(edge.get_pair_id())
        
        for edge in self.board.edges:
            if edge.state == BondState.UNDECIDED:
                if edge.get_pair_id() in placed_pairs:
                    edge.state = BondState.BLOCKED
                    return edge
        return None

    def _find_unique_move(self):
        candidates = []

        for pair, edge_list in self.board.possible_moves.items():
            valid_edges = [e for e in edge_list 
                           if e.state == BondState.UNDECIDED 
                           and not e.node_a.occupied and not e.node_b.occupied]
            
            candidates.append((len(valid_edges), valid_edges))

        candidates.sort(key=lambda x: x[0]) 

        for count, edges in candidates:
            if count == 1:
                return edges[0] 
            
            if count > 1:
                break
        
        return None

    def _find_isolated_move(self):
        for row in self.board.cells:
            for cell in row:
                if cell.occupied: continue
                valid_bonds = []
                for edge in self.board.edges:
                    if edge.state == BondState.UNDECIDED:
                        neighbor = edge.node_b if edge.node_a == cell else edge.node_a
                        if not neighbor.occupied:
                            if edge.node_a == cell or edge.node_b == cell:
                                valid_bonds.append(edge)
                if len(valid_bonds) == 1:
                    return valid_bonds[0]
        return None

    def _block_neighbors(self, node):
        for edge in self.board.edges:
            if edge.state == BondState.UNDECIDED:
                if edge.node_a == node or edge.node_b == node:
                    edge.state = BondState.BLOCKED

    def _clean_invalid_possibilities(self):
        for pair_id in list(self.board.possible_moves.keys()):
            valid = [e for e in self.board.possible_moves[pair_id] 
                     if e.state == BondState.UNDECIDED
                     and not e.node_a.occupied and not e.node_b.occupied]
            self.board.possible_moves[pair_id] = valid