from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple

class BondState(Enum):
    UNDECIDED = 0
    CONFIRMED = 1
    BLOCKED = 2

@dataclass(unsafe_hash=True)
class CellNode:
    r: int
    c: int
    value: int

    neighbors: List['CellNode'] = field(default_factory=list, hash=False, compare=False)
    edges: List['EdgeBond'] = field(default_factory=list, hash=False, compare=False)

    occupied: bool = field(default=False, compare=False)
    owner_id: int = field(default=0, compare=False)

    def __repr__(self):
        return f"({self.r},{self.c}|{self.value})"

@dataclass
class EdgeBond:
    node_a: CellNode
    node_b: CellNode
    state: BondState = BondState.UNDECIDED
    owner_id: int = 0

    def get_pair_id(self) -> Tuple[int, int]:
        return tuple(sorted((self.node_a.value, self.node_b.value)))

    def __lt__(self, other):
        return self.get_pair_id() < other.get_pair_id()

    def __repr__(self):
        return f"Edge[{self.node_a}<->{self.node_b}]"
