from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple

class BondState(Enum):
    UNDECIDED = auto()
    BLOCKED = auto()
    CONFIRMED = auto()

class StrategyLevel(Enum):
    LEVEL_1_BASIC = "Uniqueness (Basic)"
    LEVEL_2_STANDARD = "Isolation (Standard)"
    LEVEL_3_ADVANCED = "Duplicate Check (Advanced)"
    LEVEL_4_ALL = "Full Power (All Strategies)"

@dataclass
class CellNode:
    r: int
    c: int
    value: int
    neighbors: List['CellNode'] = field(default_factory=list)
    occupied: bool = False

    def __repr__(self):
        return f"{self.value}"

@dataclass
class EdgeBond:
    node_a: CellNode
    node_b: CellNode
    state: BondState = BondState.UNDECIDED
    
    def get_pair_id(self) -> Tuple[int, int]:
    
        v1 = int(self.node_a.value)
        v2 = int(self.node_b.value)


        if v1 > v2:
            return (v2, v1)
        else:
            return (v1, v2)

    def __repr__(self):
        v1, v2 = self.get_pair_id()
        return f"[{v1}|{v2}]"
