from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QPainter, QFont, QPen, QBrush

from structures import CellNode, EdgeBond, BondState
from typing import List, Tuple, Set

class DominosaBoard:
    def __init__(self, matrix: List[List[int]]):
        self.rows = len(matrix)
        self.cols = len(matrix[0])
        self.matrix_data = matrix 
        
        self.cells = [[CellNode(r, c, val) for c, val in enumerate(row)] 
                      for r, row in enumerate(matrix)]
        
        self.edges: List[EdgeBond] = []
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
                    self._create_bond(curr, self.cells[r][c+1])
                if r + 1 < self.rows:
                    self._create_bond(curr, self.cells[r+1][c])

    def _create_bond(self, n1, n2):
        bond = EdgeBond(n1, n2)
        self.edges.append(bond)
        n1.edges.append(bond)
        n2.edges.append(bond)
        n1.neighbors.append(n2)
        n2.neighbors.append(n1)

    def _init_domino_set(self):
        if not self.cells: return
        max_val = max(max(c.value for c in row) for row in self.cells)
        self.available_dominoes = {(i, j) for i in range(max_val + 1) for j in range(i, max_val + 1)}

    def get_edge(self, n1: CellNode, n2: CellNode):
        for e in n1.edges:
            if (e.node_a == n1 and e.node_b == n2) or (e.node_a == n2 and e.node_b == n1):
                return e
        return None

    def validate_move(self, node_a: CellNode, node_b: CellNode) -> bool:
        if node_b not in node_a.neighbors: return False
        if node_a.occupied or node_b.occupied: return False
        
        pair = tuple(sorted((node_a.value, node_b.value)))
        if pair not in self.available_dominoes: return False
        
        return True

    def confirm_edge(self, edge: EdgeBond, owner_id: int) -> bool:
        if edge.state == BondState.BLOCKED: return False
        
        pair = edge.get_pair_id()
        if pair not in self.available_dominoes: return False

        edge.state = BondState.CONFIRMED
        edge.owner_id = owner_id
        edge.node_a.occupied = True
        edge.node_b.occupied = True
        edge.node_a.owner_id = owner_id
        edge.node_b.owner_id = owner_id
        
        self.available_dominoes.remove(pair)
        self.placed_dominoes.add(pair)
        
        self._update_blocked_states()
        return True

    def remove_edge(self, edge: EdgeBond):
        if edge.state != BondState.CONFIRMED: return

        pair = edge.get_pair_id()
        edge.state = BondState.UNDECIDED
        edge.owner_id = 0
        edge.node_a.occupied = False
        edge.node_b.occupied = False
        edge.node_a.owner_id = 0
        edge.node_b.owner_id = 0
        
        self.placed_dominoes.remove(pair)
        self.available_dominoes.add(pair)
        
        self._update_blocked_states()

    def _update_blocked_states(self):
        for e in self.edges:
            if e.state != BondState.CONFIRMED:
                e.state = BondState.UNDECIDED

        for e in self.edges:
            if e.state == BondState.UNDECIDED:
                if e.node_a.occupied or e.node_b.occupied:
                    e.state = BondState.BLOCKED

    def has_valid_moves(self) -> bool:
        for edge in self.edges:
            if (edge.state == BondState.UNDECIDED and 
                not edge.node_a.occupied and 
                not edge.node_b.occupied and 
                edge.get_pair_id() in self.available_dominoes):
                return True
        return False

    def get_progress(self) -> float:
        if self.total_dominoes == 0: return 0.0
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
        
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.clear_flash)
        self.flash_active = False
        
        self.hint_timer = QTimer()
        self.hint_timer.timeout.connect(self.clear_hint)
        
        self.input_enabled = True 

    def set_victory(self, state):
        self.victory_mode = state
        self.repaint()

    def show_hint(self, edge):
        self.hint_edge = edge
        self.repaint()
        self.hint_timer.start(2000)

    def clear_hint(self):
        self.hint_edge = None
        self.hint_timer.stop()
        self.repaint()

    def mousePressEvent(self, e):
        if not self.input_enabled or self.victory_mode: return
        
        c = e.pos().x() // self.cell_sz
        r = e.pos().y() // self.cell_sz
        
        if 0 <= r < self.board.rows and 0 <= c < self.board.cols:
            clicked_node = self.board.cells[r][c]
            
            if clicked_node.occupied:
                for edge in clicked_node.edges:
                    if edge.state == BondState.CONFIRMED:
                        self.board.remove_edge(edge)
                        self.board_changed.emit()
                        self.repaint()
                        return

            if not self.selected_node:
                self.selected_node = clicked_node
                self.repaint()
            else:
                if clicked_node == self.selected_node:
                    self.selected_node = None 
                else:
                    if self.board.validate_move(self.selected_node, clicked_node):
                        edge = self.board.get_edge(self.selected_node, clicked_node)
                        self.move_made.emit(edge)
                        self.selected_node = None
                    else:
                        self.flash_active = True
                        self.flash_timer.start(300)
                        self.selected_node = None
                self.repaint()

    def clear_flash(self):
        self.flash_active = False
        self.flash_timer.stop()
        self.repaint()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        qp.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        
        if self.victory_mode:
            qp.fillRect(self.rect(), QColor("#FFD700"))

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                x, y = c * self.cell_sz, r * self.cell_sz
                
                bg = QColor("#FFFFFF")
                if self.victory_mode:
                    bg = QColor(255, 255, 255, 100)
                elif self.flash_active and (cell == self.selected_node or self.selected_node):
                    bg = QColor("#FFCCCC")
                elif cell == self.selected_node:
                    bg = QColor("#DDDDDD")
                
                qp.fillRect(x, y, self.cell_sz, self.cell_sz, bg)
                if not self.victory_mode:
                    qp.setPen(QColor("#EEEEEE"))
                    qp.drawRect(x, y, self.cell_sz, self.cell_sz)

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                if cell.occupied:
                    for edge in cell.edges:
                        if edge.state == BondState.CONFIRMED:
                            n = edge.node_a if edge.node_b == cell else edge.node_b
                            if (n.c > c) or (n.r > r):
                                x1, y1 = c * self.cell_sz, r * self.cell_sz
                                x2, y2 = n.c * self.cell_sz, n.r * self.cell_sz
                                
                                rect_x = min(x1, x2) + 4
                                rect_y = min(y1, y2) + 4
                                rect_w = abs(x1 - x2) + self.cell_sz - 8
                                rect_h = abs(y1 - y2) + self.cell_sz - 8
                                
                                color = QColor("#222") if cell.owner_id == 1 else QColor("#888")
                                qp.setBrush(QBrush(color))
                                qp.setPen(Qt.PenStyle.NoPen)
                                qp.drawRoundedRect(QRectF(rect_x, rect_y, rect_w, rect_h), 12, 12)

        if self.hint_edge:
            n1, n2 = self.hint_edge.node_a, self.hint_edge.node_b
            x1, y1 = n1.c * self.cell_sz + self.cell_sz/2, n1.r * self.cell_sz + self.cell_sz/2
            x2, y2 = n2.c * self.cell_sz + self.cell_sz/2, n2.r * self.cell_sz + self.cell_sz/2
            pen = QPen(QColor(200, 200, 200, 150))
            pen.setWidth(40)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            qp.setPen(pen)
            qp.drawLine(int(x1), int(y1), int(x2), int(y2))

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                x, y = c * self.cell_sz, r * self.cell_sz
                
                fg = QColor("#000000")
                if cell.occupied: fg = QColor("#FFFFFF")
                
                qp.setPen(fg)
                qp.drawText(x, y, self.cell_sz, self.cell_sz,
                            Qt.AlignmentFlag.AlignCenter, str(cell.value))

        if self.victory_mode:
            qp.setPen(QColor("#000000"))
            qp.setFont(QFont("Times New Roman", 36, QFont.Weight.Bold))
            qp.drawText(self.rect(),
                        Qt.AlignmentFlag.AlignCenter,
                        "PUZZLE SOLVED")
