from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple


class BondState(Enum):
    __slots__ = ()
    UNDECIDED = auto()
    BLOCKED = auto()
    CONFIRMED = auto()


class StrategyLevel(Enum):
    __slots__ = ()
    LEVEL_1_BASIC = "Uniqueness (Basic)"
    LEVEL_2_STANDARD = "Isolation (Standard)"
    LEVEL_3_ADVANCED = "Duplicate Check (Advanced)"
    LEVEL_4_ALL = "Full Power (All Strategies)"


@dataclass(slots=True)
class CellNode:
    r: int
    c: int
    value: int
    neighbors: List["CellNode"] = field(default_factory=list)
    occupied: bool = False

    def __repr__(self) -> str:
        return str(self.value)


@dataclass(slots=True)
class EdgeBond:
    node_a: CellNode
    node_b: CellNode
    state: BondState = BondState.UNDECIDED

    def get_pair_id(self) -> Tuple[int, int]:
        v1 = self.node_a.value
        v2 = self.node_b.value
        return (v1, v2) if v1 <= v2 else (v2, v1)

    def __repr__(self) -> str:
        v1, v2 = self.get_pair_id()
        return f"[{v1}|{v2}]"
