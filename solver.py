from structures import BondState, CellNode, EdgeBond
from board import DominosaBoard
from typing import List, Tuple, Optional, Dict, Set

class AI_Engine:
    def __init__(self, board: DominosaBoard):
        self.board = board
        self.dp_memo: Dict[Tuple[int, ...], bool] = {}
        self.nodes_visited = 0

    def get_hint_move(self, strategy="DYNAMIC_PROGRAMMING") -> Optional[EdgeBond]:
        move, _ = self.solve_next_step(strategy)
        return move

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

    def _strat_greedy(self) -> Tuple[Optional[EdgeBond], str]:
        naked_singles = self._get_naked_singles()
        self.nodes_visited += len(naked_singles)
        if naked_singles: return naked_singles[0], "Greedy: Naked Single"
            
        hidden_singles = self._get_hidden_singles()
        self.nodes_visited += len(hidden_singles)
        if hidden_singles: return hidden_singles[0], "Greedy: Hidden Single"
            
        return None, "Stuck"

    def _strat_divide_conquer(self) -> Tuple[Optional[EdgeBond], str]:
        components = self._get_connected_components()
        self.nodes_visited += len(components)
        
        if len(components) > 1:
            smallest_island = sorted(components, key=len)[0]
            move = self._solve_component(smallest_island)
            if move: return move, "D&C: Conquered Island"

        forced_edges = self._get_graph_forced_edges()
        if forced_edges: return forced_edges[0], "D&C: Forced Cut"
            
        return self._strat_greedy()

    def _strat_dynamic_programming(self) -> Tuple[Optional[EdgeBond], str]:
        candidates = self._get_all_valid_moves()
        candidates.sort(key=lambda e: self._score_move(e), reverse=True)
        
        for move in candidates:
            self.nodes_visited += 1
            if self._validate_with_dp(move):
                return move, "Dynamic Programming"
        
        return None, "No Perfect Move"
