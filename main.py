import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                             QComboBox, QFrame, QGraphicsOpacityEffect)
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QCursor, QColorConstants
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect

from board import DominosaBoard
from generator import DominosaGenerator
from solver import Solver
from structures import BondState, StrategyLevel

THEME = {
    "BG": "#FFFFFF", "TEXT": "#000000", "ACCENT": "#FF6B00", 
    "SUCCESS": "#00C853", "ERR": "#FF1744", "NUM": "#333333",
    "OVERLAY": "rgba(0, 0, 0, 180)"
}

STYLES = f"""
    QMainWindow {{ background: {THEME["BG"]}; }}
    QLabel {{ color: {THEME["TEXT"]}; font-family: 'Segoe UI'; }}
    
    QComboBox {{
        border: 2px solid #EEEEEE; border-radius: 8px; padding: 8px;
        background: white; font-weight: bold; font-family: 'Segoe UI';
    }}
    QComboBox::drop-down {{ border: 0px; }}
    
    QPushButton {{
        border: 2px solid #EEEEEE; border-radius: 8px; padding: 12px;
        background: white; font-weight: bold; font-family: 'Segoe UI';
    }}
    QPushButton:hover {{ border-color: {THEME["ACCENT"]}; color: {THEME["ACCENT"]}; }}
    
    #MenuBtn {{
        background: #111; color: white; border: none; font-size: 14px;
        padding: 18px; letter-spacing: 1px;
    }}
    #MenuBtn:hover {{ background: {THEME["ACCENT"]}; }}
    
    #HintBtn {{ background: #F5F5F5; border: none; }}
    #HintBtn:hover {{ background: {THEME["ACCENT"]}; color: white; }}
    
    #Title {{ font-size: 64px; font-weight: 900; letter-spacing: -2px; }}
    #Sub {{ color: #888; letter-spacing: 2px; font-size: 12px; font-weight: 600; margin-bottom: 30px; }}
    
    #OverlayBox {{ background: white; border-radius: 16px; padding: 40px; }}
    #WinTitle {{ font-size: 32px; font-weight: bold; margin-bottom: 10px; }}
"""

class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.hide()
        
        l = QVBoxLayout(self)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.box = QFrame()
        self.box.setObjectName("OverlayBox")
        box_l = QVBoxLayout(self.box)
        box_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl = QLabel("PUZZLE SOLVED")
        self.lbl.setObjectName("WinTitle")
        
        self.btn = QPushButton("PLAY AGAIN")
        self.btn.setObjectName("MenuBtn")
        self.btn.setFixedWidth(200)
        self.btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        box_l.addWidget(self.lbl)
        box_l.addWidget(self.btn)
        l.addWidget(self.box)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(THEME["OVERLAY"]))

class GridWidget(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.board = None
        self.cell_s, self.margin = 70, 60
        self.sel = self.hov = self.high = self.flash = None
        self.flash_c = QColor(THEME["SUCCESS"])
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: (setattr(self, 'flash', None), self.update()))
        self.setMouseTracking(True)

    def set_board(self, board):
        self.board, self.sel, self.high = board, None, None
        self.update()

    def get_cell(self, pos):
        if not self.board: return None
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cx, cy = self.margin + c * self.cell_s, self.margin + r * self.cell_s
                if (pos.x()-cx)**2 + (pos.y()-cy)**2 < (self.cell_s/2.5)**2:
                    return self.board.get_cell(r, c)
        return None

    def mousePressEvent(self, e):
        cell = self.get_cell(e.pos())
        if not cell: self.sel = None
        elif cell.occupied: self.main.break_bond(cell); self.sel = None
        elif self.main.mode == "CPU" and not self.main.human_turn: pass
        elif not self.sel: 
            self.sel = cell
            self.main.status.setText("Select adjacent number...")
        elif self.sel == cell: 
            self.sel = None
            self.main.status.setText("Ready.")
        else: 
            self.main.try_connect(self.sel, cell)
            self.sel = None
        self.update()

    def mouseMoveEvent(self, e):
        curr = self.get_cell(e.pos())
        if curr != self.hov: self.hov = curr; self.update()

    def paintEvent(self, e):
        if not self.board: return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for e in self.board.edges:
            p.setPen(Qt.PenStyle.NoPen)
            if e == self.flash: 
                p.setPen(QPen(self.flash_c, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            elif e.state == BondState.CONFIRMED: 
                p.setPen(QPen(QColor(THEME["SUCCESS"]), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            elif e == self.high: 
                p.setPen(QPen(QColor(THEME["ACCENT"]), 4, Qt.PenStyle.DashLine, Qt.PenCapStyle.RoundCap))
            
            if p.pen().style() != Qt.PenStyle.NoPen:
                x1, y1 = self.margin + e.node_a.c * self.cell_s, self.margin + e.node_a.r * self.cell_s
                x2, y2 = self.margin + e.node_b.c * self.cell_s, self.margin + e.node_b.r * self.cell_s
                p.drawLine(int(x1), int(y1), int(x2), int(y2))

        p.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.get_cell(r, c)
                cx, cy = self.margin + c * self.cell_s, self.margin + r * self.cell_s
                
                bg, txt = Qt.GlobalColor.transparent, QColor(THEME["NUM"])
                if cell.occupied: txt = QColor("#D6D3D1")
                elif cell == self.sel: bg, txt = QColor(THEME["ACCENT"]), Qt.GlobalColor.white
                elif cell == self.hov: bg = QColor("#F5F5F5")
                
                if bg != Qt.GlobalColor.transparent:
                    p.setBrush(QBrush(bg)); p.setPen(Qt.PenStyle.NoPen)
                    p.drawEllipse(QPoint(int(cx), int(cy)), 28, 28)
                
                p.setPen(txt)
                p.drawText(int(cx)-20, int(cy)-20, 40, 40, Qt.AlignmentFlag.AlignCenter, str(cell.value))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dominosa"); self.resize(1000, 800); self.setStyleSheet(STYLES)
        self.mode = "SOLO"; self.human_turn = True
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QStackedWidget(self.central)
        
        self.init_menu()
        self.init_game()
        
        self.overlay = Overlay(self.central)
        self.overlay.btn.clicked.connect(self.reset_to_menu)
        
        container = QVBoxLayout(self.central)
        container.setContentsMargins(0,0,0,0)
        container.addWidget(self.layout)

    def resizeEvent(self, event):
        self.overlay.resize(event.size())
        super().resizeEvent(event)

    def init_menu(self):
        pg = QWidget(); l = QVBoxLayout(pg); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        l.addStretch()
        l.addWidget(QLabel("DOMINOSA", objectName="Title"), 0, Qt.AlignmentFlag.AlignCenter)
        l.addWidget(QLabel("", objectName="Sub"), 0, Qt.AlignmentFlag.AlignCenter)
        
        self.sz = QComboBox()
        self.sz.addItems([f"Double-{n} Set (Grid {n+1}x{n+2})" for n in [3,4,5,6,9]])
        self.sz.setFixedWidth(320)
        l.addWidget(self.sz, 0, Qt.AlignmentFlag.AlignCenter)
        l.addSpacing(30)
        
        b1 = QPushButton("SOLO PLAY"); b1.setObjectName("MenuBtn"); b1.setFixedWidth(320)
        b1.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        b1.clicked.connect(lambda: self.start("SOLO"))
        
        b2 = QPushButton("VS COMPUTER"); b2.setObjectName("MenuBtn"); b2.setFixedWidth(320)
        b2.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        b2.clicked.connect(lambda: self.start("CPU"))
        
        l.addWidget(b1, 0, Qt.AlignmentFlag.AlignCenter)
        l.addSpacing(10)
        l.addWidget(b2, 0, Qt.AlignmentFlag.AlignCenter)
        l.addStretch()
        self.layout.addWidget(pg)

    def init_game(self):
        pg = QWidget(); l = QVBoxLayout(pg)
        
        h = QHBoxLayout(); h.setContentsMargins(30,30,30,0)
        back = QPushButton("EXIT"); back.setFixedWidth(80)
        back.clicked.connect(self.reset_to_menu)
        
        self.lbl_mode = QLabel("SOLO MODE"); self.lbl_mode.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        h.addWidget(back); h.addStretch(); h.addWidget(self.lbl_mode); h.addStretch(); h.addSpacing(80)
        
        body = QHBoxLayout()
        self.grid = GridWidget(self)
        
        side = QVBoxLayout(); side.setContentsMargins(0,40,30,40); side.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.lbl_strat = QLabel("HINT STRATEGY")
        self.strat = QComboBox()
        self.strat.addItems(["Uniqueness", "Isolation", "Duplicate Check", "Full Power"])
        self.strat.setItemData(0, StrategyLevel.LEVEL_1_BASIC)
        self.strat.setItemData(1, StrategyLevel.LEVEL_2_STANDARD)
        self.strat.setItemData(2, StrategyLevel.LEVEL_3_ADVANCED)
        self.strat.setItemData(3, StrategyLevel.LEVEL_4_ALL)
        
        self.hint_btn = QPushButton("USE HINT"); self.hint_btn.setObjectName("HintBtn")
        self.hint_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.hint_btn.clicked.connect(self.do_hint)
        
        side.addWidget(self.lbl_strat)
        side.addWidget(self.strat)
        side.addSpacing(15)
        side.addWidget(self.hint_btn)
        side.addStretch()
        
        body.addWidget(self.grid, 1); body.addLayout(side, 0)
        
        self.status = QLabel("Ready."); self.status.setObjectName("Status")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        l.addLayout(h); l.addLayout(body); l.addWidget(self.status)
        self.layout.addWidget(pg)

    def reset_to_menu(self):
        self.overlay.hide()
        self.layout.setCurrentIndex(0)

    def start(self, mode):
        self.mode = mode; self.human_turn = True
        self.lbl_mode.setText(f"{mode} MODE")
        self.lbl_mode.setStyleSheet(f"color: {THEME['ACCENT']}")
        
        n = int(self.sz.currentText().split()[0].split('-')[1])
        
        try:
            mat = DominosaGenerator.generate(n)
            self.board = DominosaBoard(mat); self.solver = Solver(self.board)
            self.grid.set_board(self.board)
            
            if mode == "SOLO":
                self.lbl_strat.setText("HINT STRATEGY")
                self.hint_btn.show()
                self.strat.setEnabled(True)
            else:
                self.lbl_strat.setText("CPU INTELLIGENCE")
                self.hint_btn.hide()
                self.strat.setEnabled(True)
            
            self.layout.setCurrentIndex(1)
        except Exception as e: print(e)

    def try_connect(self, c1, c2):
        edge = None
        for e in self.board.edges:
            if (e.node_a == c1 and e.node_b == c2) or (e.node_a == c2 and e.node_b == c1):
                edge = e; break
        
        if edge and edge.state == BondState.UNDECIDED:
            target = edge.get_pair_id()
            dup = any(e.state == BondState.CONFIRMED and e.get_pair_id() == target for e in self.board.edges)
            
            if dup:
                self.grid.flash = edge; self.grid.flash_c = QColor(THEME["ERR"])
                self.grid.timer.start(500); self.status.setText("DUPLICATE DOMINO!")
                self.grid.update()
            else:
                self.commit(edge, "HUMAN")

    def break_bond(self, cell):
        edge = next((e for e in self.board.edges if e.state == BondState.CONFIRMED and cell in (e.node_a, e.node_b)), None)
        if edge:
            edge.state = BondState.UNDECIDED
            edge.node_a.occupied = edge.node_b.occupied = False
            self.solver.rebuild_constraints()
            self.grid.update()

    def commit(self, edge, who):
        self.solver.apply_move(edge)
        self.grid.flash = edge
        self.grid.flash_c = QColor(THEME["SUCCESS"] if who == "HUMAN" else "#3B82F6")
        self.grid.timer.start(500); self.grid.update()
        
        if all(c.occupied for row in self.board.cells for c in row):
            QTimer.singleShot(500, self.overlay.show)
            return

        if self.mode == "CPU" and who == "HUMAN":
            self.human_turn = False
            self.status.setText("CPU Thinking...")
            QTimer.singleShot(1000, self.cpu_move)

    def cpu_move(self):
        strat = self.strat.currentData()
        mv, _ = self.solver.find_hint(strat)
        if mv and mv.state != BondState.BLOCKED: self.commit(mv, "CPU")
        else: self.status.setText("CPU Passes.")
        self.human_turn = True

    def do_hint(self):
        mv, r = self.solver.find_hint(self.strat.currentData())
        if not mv: self.status.setText(r); return
        
        if mv.state == BondState.BLOCKED:
            self.grid.flash = mv; self.grid.flash_c = QColor(THEME["ERR"]); self.grid.timer.start(800)
            self.status.setText("Blocking Duplicate...")
        else:
            self.grid.high = mv; self.status.setText(f"HINT: {r}")
            QTimer.singleShot(2000, lambda: (setattr(self.grid, 'high', None), self.grid.update()))
        self.grid.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow(); w.show(); sys.exit(app.exec())
