from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Tuple


class BondState(Enum):
    UNDECIDED = auto()
    BLOCKED = auto()
    CONFIRMED = auto()


@dataclass
class CellNode:
    r: int
    c: int
    value: int
    neighbors: List["CellNode"] = field(default_factory=list)
    occupied: bool = False

    def __repr__(self):
        return f"Cell({self.r}, {self.c} | Val: {self.value})"


@dataclass
class EdgeBond:
    node_a: CellNode
    node_b: CellNode
    state: BondState = BondState.UNDECIDED

    def get_pair_id(self) -> Tuple[int, int]:
        return tuple(sorted((self.node_a.value, self.node_b.value)))

    def __repr__(self):
        return f"Bond[{self.state.name}]({self.node_a} <-> {self.node_b})"
