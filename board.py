from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QPainter, QFont, QPen, QBrush
from structures import CellNode, EdgeBond, BondState
from typing import List, Tuple, Set, Dict


class DominosaBoard:
    def __init__(self, matrix: List[List[int]]):
        self.rows = len(matrix)
        self.cols = len(matrix[0])
        self.matrix_data = matrix
        self.cells = [[CellNode(r, c, val) for c, val in enumerate(row)] for r, row in enumerate(matrix)]
        self.edges: List[EdgeBond] = []
        self.edge_lookup: Dict[tuple, EdgeBond] = {}
        self.pair_edges: Dict[tuple, List[EdgeBond]] = {}
        self.available_dominoes: Set[Tuple[int, int]] = set()
        self.placed_dominoes: Set[Tuple[int, int]] = set()
        self._init_topology()
        self._init_domino_set()
        self.total_dominoes = len(self.available_dominoes)

    def _init_topology(self):
        for r in range(self.rows):
            for c in range(self.cols):
                curr = self.cells[r][c]
                if c + 1 < self.cols:
                    self._create_bond(curr, self.cells[r][c + 1])
                if r + 1 < self.rows:
                    self._create_bond(curr, self.cells[r + 1][c])

    def _create_bond(self, n1, n2):
        bond = EdgeBond(n1, n2)
        self.edges.append(bond)
        n1.edges.append(bond)
        n2.edges.append(bond)
        n1.neighbors.append(n2)
        n2.neighbors.append(n1)
        self.edge_lookup[(n1, n2)] = bond
        self.edge_lookup[(n2, n1)] = bond
        pair = tuple(sorted((n1.value, n2.value)))
        self.pair_edges.setdefault(pair, []).append(bond)

    def _init_domino_set(self):
        max_val = max(c.value for row in self.cells for c in row)
        self.available_dominoes = {(i, j) for i in range(max_val + 1) for j in range(i, max_val + 1)}

    def get_edge(self, n1: CellNode, n2: CellNode):
        return self.edge_lookup.get((n1, n2))

    def validate_move(self, node_a: CellNode, node_b: CellNode) -> bool:
        if node_b not in node_a.neighbors:
            return False
        if node_a.occupied or node_b.occupied:
            return False
        pair = tuple(sorted((node_a.value, node_b.value)))
        return pair in self.available_dominoes

    def _update_local_blocking(self, node: CellNode):
        for e in node.edges:
            if e.state == BondState.CONFIRMED:
                continue
            if e.node_a.occupied or e.node_b.occupied:
                e.state = BondState.BLOCKED
            else:
                e.state = BondState.UNDECIDED

    def confirm_edge(self, edge: EdgeBond, owner_id: int) -> bool:
        if edge.state == BondState.BLOCKED:
            return False
        pair = edge.get_pair_id()
        if pair not in self.available_dominoes:
            return False
        edge.state = BondState.CONFIRMED
        edge.owner_id = owner_id
        for n in (edge.node_a, edge.node_b):
            n.occupied = True
            n.owner_id = owner_id
        self.available_dominoes.remove(pair)
        self.placed_dominoes.add(pair)
        for e in self.pair_edges[pair]:
            if e is not edge and e.state == BondState.UNDECIDED:
                e.state = BondState.BLOCKED
        self._update_local_blocking(edge.node_a)
        self._update_local_blocking(edge.node_b)
        return True

    def remove_edge(self, edge: EdgeBond):
        if edge.state != BondState.CONFIRMED:
            return
        pair = edge.get_pair_id()
        edge.state = BondState.UNDECIDED
        edge.owner_id = 0
        for n in (edge.node_a, edge.node_b):
            n.occupied = False
            n.owner_id = 0
        self.placed_dominoes.remove(pair)
        self.available_dominoes.add(pair)
        for e in self.pair_edges[pair]:
            if e.state == BondState.BLOCKED:
                e.state = BondState.UNDECIDED
        self._update_local_blocking(edge.node_a)
        self._update_local_blocking(edge.node_b)

    def has_valid_moves(self) -> bool:
        return any(
            e.state == BondState.UNDECIDED
            and not e.node_a.occupied
            and not e.node_b.occupied
            and e.get_pair_id() in self.available_dominoes
            for e in self.edges
        )

    def get_progress(self) -> float:
        if self.total_dominoes == 0:
            return 0.0
        return len(self.placed_dominoes) / self.total_dominoes


class BoardWidget(QWidget):
    move_made = pyqtSignal(object)
    board_changed = pyqtSignal()

    def __init__(self, board):
        super().__init__()
        self.board = board
        self.cell_sz = 60
        self.setFixedSize(board.cols * self.cell_sz + 4, board.rows * self.cell_sz + 4)
        self.selected_node = None
        self.hint_edge = None
        self.victory_mode = False
        self.input_enabled = True
        self.main_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        self.win_font = QFont("Times New Roman", 36, QFont.Weight.Bold)
        self.hint_pen = QPen(QColor(200, 200, 200, 150))
        self.hint_pen.setWidth(40)
        self.hint_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.clear_flash)
        self.flash_active = False
        self.hint_timer = QTimer()
        self.hint_timer.timeout.connect(self.clear_hint)

    def set_victory(self, state):
        self.victory_mode = state
        self.update()

    def show_hint(self, edge):
        self.hint_edge = edge
        self.update()
        self.hint_timer.start(2000)

    def clear_hint(self):
        self.hint_edge = None
        self.hint_timer.stop()
        self.update()

    def mousePressEvent(self, e):
        if not self.input_enabled or self.victory_mode:
            return
        pos = e.position().toPoint()
        c = pos.x() // self.cell_sz
        r = pos.y() // self.cell_sz
        if not (0 <= r < self.board.rows and 0 <= c < self.board.cols):
            return
        node = self.board.cells[r][c]
        if node.occupied:
            for edge in node.edges:
                if edge.state == BondState.CONFIRMED:
                    self.board.remove_edge(edge)
                    self.board_changed.emit()
                    self.update()
                    return
        if not self.selected_node:
            self.selected_node = node
            self.update()
            return
        if node == self.selected_node:
            self.selected_node = None
            self.update()
            return
        if self.board.validate_move(self.selected_node, node):
            edge = self.board.get_edge(self.selected_node, node)
            self.move_made.emit(edge)
        else:
            self.flash_active = True
            self.flash_timer.start(250)
        self.selected_node = None
        self.update()

    def clear_flash(self):
        self.flash_active = False
        self.flash_timer.stop()
        self.update()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        qp.setFont(self.main_font)

        if self.victory_mode:
            qp.fillRect(self.rect(), QColor("#FFD700"))

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                x, y = c * self.cell_sz, r * self.cell_sz
                bg = QColor("#FFFFFF")
                if self.victory_mode:
                    bg = QColor(255, 255, 255, 100)
                elif self.flash_active and self.selected_node:
                    bg = QColor("#FFCCCC")
                elif cell == self.selected_node:
                    bg = QColor("#DDDDDD")
                qp.fillRect(x, y, self.cell_sz, self.cell_sz, bg)
                if not self.victory_mode:
                    qp.setPen(QColor("#EEEEEE"))
                    qp.drawRect(x, y, self.cell_sz, self.cell_sz)

        for edge in self.board.edges:
            if edge.state == BondState.CONFIRMED:
                a, b = edge.node_a, edge.node_b
                if (b.c > a.c) or (b.r > a.r):
                    x1, y1 = a.c * self.cell_sz, a.r * self.cell_sz
                    x2, y2 = b.c * self.cell_sz, b.r * self.cell_sz
                    rect_x = min(x1, x2) + 4
                    rect_y = min(y1, y2) + 4
                    rect_w = abs(x1 - x2) + self.cell_sz - 8
                    rect_h = abs(y1 - y2) + self.cell_sz - 8
                    color = QColor("#222") if a.owner_id == 1 else QColor("#888")
                    qp.setBrush(QBrush(color))
                    qp.setPen(Qt.PenStyle.NoPen)
                    qp.drawRoundedRect(QRectF(rect_x, rect_y, rect_w, rect_h), 12, 12)

        if self.hint_edge:
            n1, n2 = self.hint_edge.node_a, self.hint_edge.node_b
            x1 = n1.c * self.cell_sz + self.cell_sz / 2
            y1 = n1.r * self.cell_sz + self.cell_sz / 2
            x2 = n2.c * self.cell_sz + self.cell_sz / 2
            y2 = n2.r * self.cell_sz + self.cell_sz / 2
            qp.setPen(self.hint_pen)
            qp.drawLine(int(x1), int(y1), int(x2), int(y2))

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                x, y = c * self.cell_sz, r * self.cell_sz
                fg = QColor("#000000")
                if cell.occupied:
                    fg = QColor("#FFFFFF")
                qp.setPen(fg)
                qp.drawText(x, y, self.cell_sz, self.cell_sz,
                            Qt.AlignmentFlag.AlignCenter, str(cell.value))

        if self.victory_mode:
            qp.setPen(QColor("#000000"))
            qp.setFont(self.win_font)
            qp.drawText(self.rect(),
                        Qt.AlignmentFlag.AlignCenter,
                        "PUZZLE SOLVED")
