from structures import BondState, CellNode, EdgeBond
from board import DominosaBoard
from typing import List, Tuple, Optional, Dict, Set


class SolverEngine:
    def __init__(self, board: DominosaBoard):
        self.board = board
        self.dp_memo: Dict[Tuple[int, ...], bool] = {}
        self.nodes_visited = 0
    
# Helper Function
    def _get_all_valid_moves(self) -> List[EdgeBond]:
        moves = []
        for e in self.board.edges:
            if (e.state == BondState.UNDECIDED and
                not e.node_a.occupied and
                not e.node_b.occupied and
                e.get_pair_id() in self.board.available_dominoes):
                moves.append(e)
        return moves

    def _get_any_valid_move(self) -> Optional[EdgeBond]:
        moves = self._get_all_valid_moves()
        if moves:
            return moves[0]
        return None

    def _get_connected_components(self) -> List[Set[CellNode]]:
        visited = set()
        components = []
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                if not cell.occupied and cell not in visited:
                    island = set()
                    q = [cell]
                    visited.add(cell)
                    while q:
                        curr = q.pop(0)
                        island.add(curr)
                        for e in curr.edges:
                            if e.state == BondState.UNDECIDED:
                                n = e.node_a if e.node_b == curr else e.node_b
                                if not n.occupied and n not in visited:
                                    visited.add(n)
                                    q.append(n)
                    components.append(island)
        return components

    def _solve_component(self, island: Set[CellNode]) -> Optional[EdgeBond]:
        for cell in island:
            valid = [e for e in cell.edges
                     if e.state == BondState.UNDECIDED
                     and not e.node_a.occupied
                     and not e.node_b.occupied
                     and e.get_pair_id() in self.board.available_dominoes]
            if valid:
                return valid[0]
        return None

    def _score_move(self, edge: EdgeBond) -> int:
        score = 0
        n1_deg = len([e for e in edge.node_a.edges if e.state == BondState.UNDECIDED])
        n2_deg = len([e for e in edge.node_b.edges if e.state == BondState.UNDECIDED])
        if n1_deg == 1 or n2_deg == 1:
            score += 10
        return score

    def _validate_with_dp(self, move: EdgeBond) -> bool:
        mask = [1 if c.occupied or c in [move.node_a, move.node_b] else 0
                for row in self.board.cells for c in row]
        self.dp_memo = {}
        return self._can_tile(tuple(mask), self.board.cols)

    def _can_tile(self, mask, width):
        if all(mask):
            return True
        if mask in self.dp_memo:
            return self.dp_memo[mask]

        idx = mask.index(0)
        res = False

        if (idx % width) + 1 < width and idx + 1 < len(mask) and mask[idx + 1] == 0:
            m = list(mask)
            m[idx] = 1
            m[idx + 1] = 1
            if self._can_tile(tuple(m), width):
                res = True

        if not res and idx + width < len(mask) and mask[idx + width] == 0:
            m = list(mask)
            m[idx] = 1
            m[idx + width] = 1
            if self._can_tile(tuple(m), width):
                res = True

        self.dp_memo[mask] = res
        return res

    def _get_naked_singles(self) -> List[EdgeBond]:
        moves = []
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                if cell.occupied:
                    continue
                valid = [e for e in cell.edges
                         if e.state == BondState.UNDECIDED
                         and not e.node_a.occupied
                         and not e.node_b.occupied
                         and e.get_pair_id() in self.board.available_dominoes]
                if len(valid) == 1:
                    moves.append(valid[0])
        return moves

    def _get_hidden_singles(self) -> List[EdgeBond]:
        moves = []
        for pair in list(self.board.available_dominoes):
            candidates = [e for e in self.board.edges
                          if e.state == BondState.UNDECIDED
                          and not e.node_a.occupied
                          and not e.node_b.occupied
                          and e.get_pair_id() == pair]
            if len(candidates) == 1:
                moves.append(candidates[0])
        return moves

    def _get_graph_forced_edges(self) -> List[EdgeBond]:
        adj = {}
        all_potential = []

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                if cell.occupied or (r + c) % 2 != 0:
                    continue

                neighbors = [e.node_a if e.node_b == cell else e.node_b
                             for e in cell.edges
                             if e.state != BondState.BLOCKED
                             and not (e.node_a.occupied or e.node_b.occupied)
                             and e.get_pair_id() in self.board.available_dominoes]

                adj[cell] = neighbors
                for v in neighbors:
                    all_potential.append((cell, v))

        base_match = self._calc_max_matching(adj)
        forced = []
        seen = set()

        for u, v in all_potential:
            key = tuple(sorted((id(u), id(v))))
            if key in seen:
                continue
            seen.add(key)

            if v in adj[u]:
                adj[u].remove(v)
                if self._calc_max_matching(adj) < base_match:
                    for e in u.edges:
                        if e.node_a == v or e.node_b == v:
                            forced.append(e)
                adj[u].append(v)

        return forced

    def _calc_max_matching(self, adj):
        match = {}
        count = 0
        for u in adj:
            if self._dfs_match(u, adj, set(), match):
                count += 1
        return count

    def _dfs_match(self, u, adj, visited, match):
        for v in adj[u]:
            if v not in visited:
                visited.add(v)
                if v not in match or self._dfs_match(match[v], adj, visited, match):
                    match[v] = u
                    return True
        return False
# STRATEGY ALGORITHMS 

    def _strat_greedy(self) -> Tuple[Optional[EdgeBond], str]:
        naked_singles = self._get_naked_singles()
        self.nodes_visited += len(naked_singles)
        if naked_singles:
            return naked_singles[0], "Greedy: Naked Single"

        hidden_singles = self._get_hidden_singles()
        self.nodes_visited += len(hidden_singles)
        if hidden_singles:
            return hidden_singles[0], "Greedy: Hidden Single"

        return None, "Stuck"

    def _strat_divide_conquer(self) -> Tuple[Optional[EdgeBond], str]:
        components = self._get_connected_components()
        self.nodes_visited += len(components)

        if len(components) > 1:
            smallest_island = sorted(components, key=len)[0]
            move = self._solve_component(smallest_island)
            if move:
                return move, "D&C: Conquered Island"

        forced_edges = self._get_graph_forced_edges()
        if forced_edges:
            return forced_edges[0], "D&C: Forced Cut"

        return self._strat_greedy()

    def _strat_dynamic_programming(self) -> Tuple[Optional[EdgeBond], str]:
        candidates = self._get_all_valid_moves()
        candidates.sort(key=lambda e: self._score_move(e), reverse=True)

        for move in candidates:
            self.nodes_visited += 1
            if self._validate_with_dp(move):
                return move, "Dynamic Programming"

        return None, "No Perfect Move"

    def solve_next_step(self, strategy="DYNAMIC_PROGRAMMING") -> Tuple[Optional[EdgeBond], str]:
        self.nodes_visited = 0
        move, reason = None, "Stuck"

        if strategy == "GREEDY":
            move, reason = self._strat_greedy()
        elif strategy == "DIVIDE_CONQUER":
            move, reason = self._strat_divide_conquer()
        elif strategy == "DYNAMIC_PROGRAMMING":
            move, reason = self._strat_dynamic_programming()

        if move is None:
            fallback = self._get_any_valid_move()
            if fallback:
                return fallback, f"{strategy} (Fallback)"

        return move, reason

    def get_hint_move(self, strategy="DYNAMIC_PROGRAMMING") -> Optional[EdgeBond]:
        move, _ = self.solve_next_step(strategy)
        return move
