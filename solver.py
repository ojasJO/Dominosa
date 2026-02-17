import time
from structures import BondState

class HybridSolver:
    def __init__(self, board, callback=None):
        self.board = board
        self.callback = callback
        self.dp_memo = {}

    def log(self, msg, cells=[]):
        if self.callback: self.callback(msg, cells)


    def get_singles(self):              
        moves = []
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                if cell.occupied: continue
                
               
                valid = [e for e in cell.edges if e.state == BondState.UNDECIDED 
                         and not e.node_a.occupied and not e.node_b.occupied
                         and e.get_pair_id() in self.board.available]
                
                if len(valid) == 1: moves.append(valid[0])
        return moves


    def get_hidden_singles(self):       
        self.log("Scanning Hidden Singles...", [])
        moves = []
        for pair in list(self.board.available):
            candidates = [e for e in self.board.edges 
                          if e.state == BondState.UNDECIDED 
                          and not e.node_a.occupied and not e.node_b.occupied
                          and e.get_pair_id() == pair]
            if len(candidates) == 1: moves.append(candidates[0])
        return moves


    def get_forced_edges(self):
        self.log("Analyzing Graph Topology...", [])
        adj = {}
        all_edges = []
        

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                if cell.occupied or (r+c)%2 != 0: continue
                
                valid = [e.node_a if e.node_b==cell else e.node_b for e in cell.edges
                         if e.state != BondState.BLOCKED and not (e.node_a.occupied or e.node_b.occupied)
                         and e.get_pair_id() in self.board.available]
                adj[cell] = valid
                for v in valid: all_edges.append((cell, v))


        base_match = self._match(adj)
        forced = []
        

        seen_edges = set()
        for u, v in all_edges:
            pair_key = tuple(sorted((id(u), id(v))))
            if pair_key in seen_edges: continue
            seen_edges.add(pair_key)


            if v in adj[u]:
                adj[u].remove(v)
                if self._match(adj) < base_match:

                    for e in u.edges:
                        if (e.node_a==v or e.node_b==v): forced.append(e)
                adj[u].append(v)
        return forced

    def _match(self, adj):
        match, count = {}, 0
        for u in adj:
            if self._dfs(u, adj, set(), match): count += 1
        return count

    def _dfs(self, u, adj, vis, match):
        for v in adj[u]:
            if v not in vis:
                vis.add(v)
                if v not in match or self._dfs(match[v], adj, vis, match):
                    match[v] = u
                    return True
        return False


    def check_dp(self, move):

        mask = [1 if c.occupied or c in [move.node_a, move.node_b] else 0 
                for row in self.board.cells for c in row]
        self.dp_memo = {}
        return self._can_tile(tuple(mask), self.board.cols)

    def _can_tile(self, mask, w):
        if all(mask): return True
        if mask in self.dp_memo: return self.dp_memo[mask]
        
        i = mask.index(0)

        res = False
        if (i%w)+1 < w and i+1 < len(mask) and mask[i+1] == 0:
            m = list(mask); m[i]=m[i+1]=1
            if self._can_tile(tuple(m), w): res = True
        
        if not res and i+w < len(mask) and mask[i+w] == 0:
            m = list(mask); m[i]=m[i+w]=1
            if self._can_tile(tuple(m), w): res = True

        self.dp_memo[mask] = res
        return res


    def solve_step(self):

        for m in self.get_naked_singles():
            if self.check_dp(m): return m, "Greedy"
            

        for m in self.get_hidden_singles():
            if self.check_dp(m): return m, "Hidden Single"


        if forced := self.get_forced_edges(): return forced[0], "Graph Force"
        
        return None, "Stuck"
