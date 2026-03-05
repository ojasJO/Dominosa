from structures import BondState, CellNode, EdgeBond
from board import DominosaBoard
from typing import List, Tuple, Optional, Dict, Set, FrozenSet

class SolverEngine:
    def __init__(self, board: DominosaBoard):
        self.board = board
        self.dp_memo: Dict[Tuple[int, FrozenSet[Tuple[int, int]]], bool] = {}
        self.nodes_visited = 0
        self.is_cancelled = False 

    def _apply_move(self, move: EdgeBond):
        move.node_a.occupied = True
        move.node_b.occupied = True
        move.state = BondState.CONFIRMED
        self.board.available_dominoes.remove(move.get_pair_id())

    def _undo_move(self, move: EdgeBond):
        move.node_a.occupied = False
        move.node_b.occupied = False
        move.state = BondState.UNDECIDED
        self.board.available_dominoes.add(move.get_pair_id())

    def _forward_check(self) -> bool:
        for pair in self.board.available_dominoes:
            has_candidate = any(
                e for e in self.board.edges
                if e.state == BondState.UNDECIDED
                and not e.node_a.occupied
                and not e.node_b.occupied
                and e.get_pair_id() == pair
            )
            if not has_candidate:
                return False
        return True

    def _get_state_key(self) -> Tuple[int, FrozenSet[Tuple[int, int]]]:
        occupancy = 0
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                if self.board.cells[r][c].occupied:
                    occupancy |= (1 << (r * self.board.cols + c))
        return (occupancy, frozenset(self.board.available_dominoes))

    def _get_all_valid_moves(self) -> List[EdgeBond]:
        return [e for e in self.board.edges
                if e.state == BondState.UNDECIDED
                and not e.node_a.occupied
                and not e.node_b.occupied
                and e.get_pair_id() in self.board.available_dominoes]

    def _score_move(self, edge: EdgeBond) -> int:
        score = 0
        n1_deg = sum(1 for e in edge.node_a.edges if e.state == BondState.UNDECIDED)
        n2_deg = sum(1 for e in edge.node_b.edges if e.state == BondState.UNDECIDED)
        if n1_deg == 1 or n2_deg == 1:
            score += 10
        return score

    def _pick_most_constrained_pair(self) -> Optional[Tuple[int, int]]:
        if not self.board.available_dominoes:
            return None
            
        counts = {pair: 0 for pair in self.board.available_dominoes}
        
        for e in self.board.edges:
            if e.state == BondState.UNDECIDED and not e.node_a.occupied and not e.node_b.occupied:
                pair = e.get_pair_id()
                if pair in counts:
                    counts[pair] += 1
                    
        best_pair = None
        min_candidates = float('inf')
        for pair, count in counts.items():
            if count < min_candidates:
                min_candidates = count
                best_pair = pair
                
        return best_pair

    def _validate_with_dp(self) -> bool:
        W, H = self.board.cols, self.board.rows
        grid = [[False for _ in range(W)] for _ in range(H)]
        for r in range(H):
            for c in range(W):
                if self.board.cells[r][c].occupied:
                    grid[r][c] = True
        return self._can_tile_bottom_up(grid, W, H)

    def _can_tile_bottom_up(self, grid: List[List[bool]], W: int, H: int) -> bool:
        dp = {0: True}
        for i in range(W * H):
            next_dp = {}
            r, c = i // W, i % W
            is_filled = grid[r][c]
            
            for mask in dp:
                if mask & 1: 
                    if not is_filled:
                        next_dp[mask >> 1] = True
                else:
                    if is_filled:
                        next_dp[mask >> 1] = True
                    else:
                        if c + 1 < W and not grid[r][c + 1] and not (mask & 2):
                            next_dp[(mask >> 1) | 1] = True
                        if r + 1 < H and not grid[r + 1][c]:
                            next_dp[(mask >> 1) | (1 << (W - 1))] = True
            
            dp = next_dp
            if not dp:
                return False
        return 0 in dp

    def _validate_with_backtrack(self) -> bool:
        W, H = self.board.cols, self.board.rows
        grid = [[False for _ in range(W)] for _ in range(H)]
        for r in range(H):
            for c in range(W):
                if self.board.cells[r][c].occupied:
                    grid[r][c] = True
        return self._solve_backtrack(grid, W, H, 0)

    def _solve_backtrack(self, grid: List[List[bool]], W: int, H: int, idx: int) -> bool:
        self.nodes_visited += 1
        
        while idx < W * H and grid[idx // W][idx % W]:
            idx += 1
            
        if idx == W * H:
            return True
            
        r, c = idx // W, idx % W
        
        if c + 1 < W and not grid[r][c + 1]:
            grid[r][c] = grid[r][c + 1] = True
            if self._solve_backtrack(grid, W, H, idx + 1):
                return True
            grid[r][c] = grid[r][c + 1] = False
            
        if r + 1 < H and not grid[r + 1][c]:
            grid[r][c] = grid[r + 1][c] = True
            if self._solve_backtrack(grid, W, H, idx + 1):
                return True
            grid[r][c] = grid[r + 1][c] = False
            
        return False

    def _get_naked_singles(self) -> List[EdgeBond]:
        moves = []
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                if cell.occupied: continue
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

    def _strat_greedy(self) -> Tuple[Optional[EdgeBond], str]:
        naked_singles = self._get_naked_singles()
        self.nodes_visited += len(naked_singles)
        if naked_singles:
            return naked_singles[0], "Greedy: Naked Single"

        hidden_singles = self._get_hidden_singles()
        self.nodes_visited += len(hidden_singles)
        if hidden_singles:
            return hidden_singles[0], "Greedy: Hidden Single"

        return None, "Greedy Exhausted"

    def _solve_region(self, region: List[CellNode]) -> List[EdgeBond]:
        if self.is_cancelled: return []
        if len(region) <= 4:
            return self._trivial_solution(region)
            
        left_region, right_region = self._split_region(region)
        left_solution = self._solve_region(left_region)
        right_solution = self._solve_region(right_region)
        
        return self._combine_regions(left_solution, right_solution)

    def _split_region(self, region: List[CellNode]) -> Tuple[List[CellNode], List[CellNode]]:
        if not region: return [], []
        
        min_r, max_r = min(c.r for c in region), max(c.r for c in region)
        min_c, max_c = min(c.c for c in region), max(c.c for c in region)
        
        left, right = [], []
        if (max_c - min_c) >= (max_r - min_r):
            mid_c = (min_c + max_c) // 2
            for c in region:
                if c.c <= mid_c: left.append(c)
                else: right.append(c)
        else:
            mid_r = (min_r + max_r) // 2
            for c in region:
                if c.r <= mid_r: left.append(c)
                else: right.append(c)
                
        if not left or not right:
            mid = len(region) // 2
            return region[:mid], region[mid:]
            
        return left, right

    def _trivial_solution(self, region: List[CellNode]) -> List[EdgeBond]:
        solution = []
        free_cells = set(region)
        
        for u in list(free_cells):
            if u not in free_cells: continue
            for e in u.edges:
                v = e.node_a if e.node_b == u else e.node_b
                if (v in free_cells and e.state != BondState.BLOCKED and 
                    e.get_pair_id() in self.board.available_dominoes):
                    solution.append(e)
                    free_cells.remove(u)
                    free_cells.remove(v)
                    break
        return solution

    def _combine_regions(self, left: List[EdgeBond], right: List[EdgeBond]) -> List[EdgeBond]:
        left_nodes = {n for e in left for n in (e.node_a, e.node_b)}
        right_nodes = {n for e in right for n in (e.node_a, e.node_b)}
        
        boundary = set()
        for u in left_nodes:
            for e in u.edges:
                v = e.node_a if e.node_b == u else e.node_b
                if v in right_nodes:
                    boundary.add(u)
                    boundary.add(v)
                    
        merged = left + right
        broken = []
        
        for e in merged[:]:
            if e.node_a in boundary or e.node_b in boundary:
                merged.remove(e)
                broken.append(e)
                
        free_cells = {n for e in broken for n in (e.node_a, e.node_b)}
        
        cross_edges = []
        for u in free_cells:
            for e in u.edges:
                v = e.node_a if e.node_b == u else e.node_b
                if v in free_cells and e.get_pair_id() in self.board.available_dominoes:
                    if (u in left_nodes and v in right_nodes) or (v in left_nodes and u in right_nodes):
                        if e not in cross_edges: cross_edges.append(e)
                        
        for e in cross_edges:
            if e.node_a in free_cells and e.node_b in free_cells:
                merged.append(e)
                free_cells.remove(e.node_a)
                free_cells.remove(e.node_b)
                
        local_edges = []
        for u in free_cells:
            for e in u.edges:
                v = e.node_a if e.node_b == u else e.node_b
                if v in free_cells and e.get_pair_id() in self.board.available_dominoes:
                    if e not in local_edges: local_edges.append(e)
                    
        for e in local_edges:
            if e.node_a in free_cells and e.node_b in free_cells:
                merged.append(e)
                free_cells.remove(e.node_a)
                free_cells.remove(e.node_b)
                
        if free_cells:
            rescue = self._trivial_solution(list(free_cells))
            merged.extend(rescue)
                
        return merged

    def _strat_divide_conquer(self) -> Tuple[Optional[EdgeBond], str]:
        empty_cells = [c for row in self.board.cells for c in row if not c.occupied]
        if not empty_cells:
            return None, "D&C Exhausted"
            
        self.nodes_visited += len(empty_cells)
        solution = self._solve_region(empty_cells)
        
        for edge in solution:
            if (edge.state == BondState.UNDECIDED and not edge.node_a.occupied and 
                not edge.node_b.occupied and edge.get_pair_id() in self.board.available_dominoes):
                return edge, "Divide & Conquer (Classical)"
                
        return None, "D&C Exhausted"

    def _strat_backtracking(self) -> Tuple[Optional[EdgeBond], str]:
        if self.is_cancelled:
            return None, "Cancelled"

        pair = self._pick_most_constrained_pair()
        if pair is None:
            return None, "Backtracking Exhausted"
            
        candidates = [e for e in self.board.edges
                      if e.state == BondState.UNDECIDED
                      and not e.node_a.occupied
                      and not e.node_b.occupied
                      and e.get_pair_id() == pair]
                      
        for edge in candidates:
            self.nodes_visited += 1
            self._apply_move(edge)
            
            if self._forward_check() and self._validate_with_backtrack():
                self._undo_move(edge)
                return edge, "Backtracking (DFS)"
                
            self._undo_move(edge)
            
        return None, "Backtracking Exhausted"

    def _is_solvable_dp(self) -> bool:
        if self.is_cancelled:
            return False

        key = self._get_state_key()
        if key in self.dp_memo:
            return self.dp_memo[key]
            
        if not self._validate_with_dp():
            self.dp_memo[key] = False
            return False
            
        if not self.board.available_dominoes:
            self.dp_memo[key] = True
            return True
            
        candidates = self._get_all_valid_moves()
        if not candidates:
            self.dp_memo[key] = False
            return False
            
        candidates.sort(key=lambda e: self._score_move(e), reverse=True)
        
        for move in candidates:
            self.nodes_visited += 1
            self._apply_move(move)
            
            if self._forward_check():
                if self._is_solvable_dp():
                    self._undo_move(move)
                    self.dp_memo[key] = True
                    return True
                    
            self._undo_move(move)
            
        self.dp_memo[key] = False
        return False

    def _strat_dynamic_programming(self) -> Tuple[Optional[EdgeBond], str]:
        candidates = self._get_all_valid_moves()
        candidates.sort(key=lambda e: self._score_move(e), reverse=True)
        
        for move in candidates:
            self.nodes_visited += 1
            self._apply_move(move)
            
            if self._forward_check() and self._is_solvable_dp():
                self._undo_move(move)
                return move, "Dynamic Programming"
                
            self._undo_move(move)
            
        return None, "DP Exhausted"

    def solve_next_step(self, strategy="DYNAMIC_PROGRAMMING") -> Tuple[Optional[EdgeBond], str]:
        self.nodes_visited = 0
        self.is_cancelled = False 
        
        if strategy == "GREEDY":
            return self._strat_greedy()
        elif strategy == "DIVIDE_CONQUER":
            return self._strat_divide_conquer()
        elif strategy == "DYNAMIC_PROGRAMMING":
            return self._strat_dynamic_programming()
        elif strategy == "BACKTRACKING":
            return self._strat_backtracking()
            
        return None, f"{strategy} Exhausted"

    def get_hint_move(self, strategy="DYNAMIC_PROGRAMMING") -> Optional[EdgeBond]:
        move, _ = self.solve_next_step(strategy)
        return move
