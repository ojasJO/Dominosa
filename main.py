import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QComboBox, QFrame)
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QCursor
from PyQt6.QtCore import Qt, QTimer, QPoint

from board import DominosaBoard
from puzzles import PuzzleDB
from solver import Solver
from structures import BondState, StrategyLevel
from game_controller import GameController


THEME = {
    "BG": "#FFFFFF", "TEXT": "#000000", "ACCENT": "#FF6B00",
    "SUCCESS": "#00C853", "ERR": "#FF1744", "NUM": "#333333",
    "OVERLAY": "rgba(0,0,0,180)"
}


# ---------- OVERLAY ----------
class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()

        l = QVBoxLayout(self)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.box = QFrame()
        box_l = QVBoxLayout(self.box)

        self.lbl = QLabel("PUZZLE SOLVED")
        self.btn = QPushButton("PLAY AGAIN")

        box_l.addWidget(self.lbl)
        box_l.addWidget(self.btn)
        l.addWidget(self.box)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(THEME["OVERLAY"]))


# ---------- GRID ----------
class GridWidget(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.board = None
        self.cell_s = 70
        self.margin = 60
        self.sel = None
        self.hov = None
        self.flash = None
        self.flash_c = QColor(THEME["SUCCESS"])

        self.timer = QTimer()
        self.timer.timeout.connect(self.clear_flash)

        self.setMouseTracking(True)

    def clear_flash(self):
        self.flash = None
        self.update()

    def set_board(self, board):
        self.board = board
        self.sel = None
        self.update()

    def get_cell(self, pos):
        if not self.board:
            return None

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cx = self.margin + c * self.cell_s
                cy = self.margin + r * self.cell_s
                if (pos.x()-cx)**2 + (pos.y()-cy)**2 < (self.cell_s/2.5)**2:
                    return self.board.get_cell(r, c)
        return None
def mousePressEvent(self, e):
    cell = self.get_cell(e.pos())

    # Case 1: Click outside grid
    if not cell:
        self.sel = None
        self.update()
        return

    # Case 2: Click occupied cell → break bond
    if cell.occupied:
        self.main.break_bond(cell)
        self.sel = None
        self.update()
        return

    # Case 3: CPU mode and not human's turn → ignore click
    if self.main.mode == "CPU" and not self.main.human_turn:
        return

    # Case 4: No selection yet → select first cell
    if not self.sel:
        self.sel = cell
        self.main.status.setText("Select adjacent number...")
        self.update()
        return

    # Case 5: Clicking same cell → deselect
    if self.sel == cell:
        self.sel = None
        self.main.status.setText("Ready.")
        self.update()
        return

    # Case 6: Try connecting two different cells
    self.main.try_connect(self.sel, cell)
    self.sel = None
    self.update()


    def paintEvent(self, e):
        if not self.board:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # edges
        for ed in self.board.edges:
            if ed.state == BondState.CONFIRMED:
                p.setPen(QPen(QColor(THEME["SUCCESS"]), 5))
                x1 = self.margin + ed.node_a.c * self.cell_s
                y1 = self.margin + ed.node_a.r * self.cell_s
                x2 = self.margin + ed.node_b.c * self.cell_s
                y2 = self.margin + ed.node_b.r * self.cell_s
                p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # nodes
        p.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.get_cell(r, c)
                cx = self.margin + c * self.cell_s
                cy = self.margin + r * self.cell_s

                if cell == self.sel:
                    p.setBrush(QBrush(QColor(THEME["ACCENT"])))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawEllipse(QPoint(int(cx), int(cy)), 28, 28)

                p.setPen(QColor(THEME["NUM"]))
                p.drawText(int(cx)-20, int(cy)-20, 40, 40,
                           Qt.AlignmentFlag.AlignCenter, str(cell.value))


# ---------- MAIN WINDOW ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dominosa")
        self.resize(1000, 800)

        self.layout = QVBoxLayout()
        w = QWidget()
        w.setLayout(self.layout)
        self.setCentralWidget(w)

        self.grid = GridWidget(self)
        self.layout.addWidget(self.grid)

        self.status = QLabel("Ready.")
        self.layout.addWidget(self.status)

        self.start_game()

    def start_game(self):
        mat = PuzzleDB.get_board(4)

        self.board = DominosaBoard(mat)
        self.solver = Solver(self.board)

        # DIVIDE & CONQUER ENTRY POINT
        self.controller = GameController(self.board, self.solver)

        self.grid.set_board(self.board)

    def handle_move(self, c1, c2):
        result, edge = self.controller.try_connect(c1, c2)

        if result == "duplicate":
            self.status.setText("Duplicate domino!")
            self.grid.flash = edge
            self.grid.flash_c = QColor(THEME["ERR"])
            self.grid.timer.start(600)

        elif result == "success":
            self.status.setText("Move applied.")
            self.grid.flash = edge
            self.grid.flash_c = QColor(THEME["SUCCESS"])
            self.grid.timer.start(600)

        if self.controller.is_solved():
            self.status.setText("PUZZLE SOLVED!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

