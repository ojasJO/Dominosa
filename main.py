import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QTextEdit, QLabel
)
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt

from board import DominosaBoard
from solver import Solver
from structures import BondState


class GridWidget(QWidget):
    def __init__(self, board):
        super().__init__()
        self.board = board
        self.cell_size = 60
        self.margin = 40
        self.setMinimumSize(400, 400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                x = self.margin + c * self.cell_size
                y = self.margin + r * self.cell_size
                val = str(self.board.get_cell(r, c).value)
                rect = painter.boundingRect(
                    x, y, self.cell_size, self.cell_size,
                    Qt.AlignmentFlag.AlignCenter, val
                )
                painter.drawText(
                    x + (self.cell_size - rect.width()) // 2,
                    y + (self.cell_size + rect.height()) // 2 - 5,
                    val
                )

        for edge in self.board.edges:
            self._draw_edge(painter, edge)

    def _draw_edge(self, painter, edge):
        x1 = self.margin + edge.node_a.c * self.cell_size + self.cell_size // 2
        y1 = self.margin + edge.node_a.r * self.cell_size + self.cell_size // 2
        x2 = self.margin + edge.node_b.c * self.cell_size + self.cell_size // 2
        y2 = self.margin + edge.node_b.r * self.cell_size + self.cell_size // 2

        if edge.state == BondState.CONFIRMED:
            painter.setPen(QPen(QColor(0, 200, 0), 6))
            painter.drawLine(x1, y1, x2, y2)

        elif edge.state == BondState.BLOCKED:
            painter.setPen(QPen(QColor(200, 0, 0), 3))
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            if x1 == x2:
                painter.drawLine(int(mx - 10), int(my), int(mx + 10), int(my))
            else:
                painter.drawLine(int(mx), int(my - 10), int(mx), int(my + 10))

        else:
            pen = QPen(QColor(200, 200, 200), 2)
            pen.setStyle(Qt.PenStyle.DotLine)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)


class DominosaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dominosa Solver - Phase 1 Architect")
        self.setGeometry(100, 100, 900, 600)

        matrix = np.array([[0, 0, 1, 1]])
        self.board = DominosaBoard(matrix)
        self.solver = Solver(self.board)

        main_layout = QHBoxLayout()
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.grid_widget = GridWidget(self.board)
        main_layout.addWidget(self.grid_widget, stretch=2)

        control_panel = QVBoxLayout()
        self.btn_step = QPushButton("Step Logic (Single Pass)")
        self.btn_step.clicked.connect(self.run_step)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        control_panel.addWidget(QLabel("Controls:"))
        control_panel.addWidget(self.btn_step)
        control_panel.addWidget(QLabel("Logic Log:"))
        control_panel.addWidget(self.log_box)

        main_layout.addLayout(control_panel, stretch=1)

    def run_step(self):
        moved = self.solver.step()
        if self.solver.log:
            self.log_box.setText("\n".join(self.solver.log))
        if not moved:
            self.log_box.append(">> Logic Stuck or Finished.")
        self.grid_widget.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DominosaWindow()
    window.show()
    sys.exit(app.exec())
