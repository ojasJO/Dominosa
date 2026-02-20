import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QComboBox, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF
from PyQt6.QtGui import QColor, QPainter, QFont, QPen, QBrush

from board import DominosaBoard
from solver import SolverEngine
from avatars import AvatarWidget
from structures import BondState

GRID_HARD = [
    [5, 2, 4, 1, 6, 2, 1, 3], 
    [5, 5, 4, 3, 6, 2, 4, 6],
    [0, 1, 0, 4, 1, 2, 6, 6], 
    [3, 0, 3, 5, 2, 0, 5, 4],
    [4, 4, 3, 1, 2, 6, 0, 1], 
    [1, 2, 3, 0, 5, 6, 3, 1],
    [3, 2, 4, 5, 6, 0, 0, 5]
]

STRATEGIES = ["GREEDY", "DIVIDE_CONQUER", "DYNAMIC_PROGRAMMING"]

STYLES = """
    QMainWindow { background-color: #FAFAFA; }
    QWidget { background-color: #FAFAFA; color: #111; font-family: 'Segoe UI', sans-serif; }
    
    QLabel#Title { font-family: 'Georgia', serif; font-size: 64px; letter-spacing: 4px; color: #000; }
    QLabel#Subtitle { font-size: 14px; letter-spacing: 2px; color: #666; text-transform: uppercase; }
    
    QPushButton {
        border: 1px solid #CCC; padding: 12px 24px; font-size: 13px; min-width: 140px;
        background: #FFF; color: #000; border-radius: 4px; font-weight: 500;
    }
    QPushButton:hover { background: #F0F0F0; border-color: #999; }
    QPushButton:pressed { background: #E0E0E0; }
    QPushButton:disabled { color: #BBB; border-color: #EEE; background: #FCFCFC; }
    
    QPushButton#ActionBtn {
        background-color: #111; color: #FFF; border: none; font-weight: bold;
    }
    QPushButton#ActionBtn:hover { background-color: #333; }
    
    QComboBox { 
        border: 1px solid #CCC; padding: 6px; min-width: 160px; 
        background: #FFF; border-radius: 4px;
    }
"""

class StrategyWorker(QThread):
    finished = pyqtSignal(object, str, int) 
    
    def __init__(self, engine, strategy):
        super().__init__()
        self.engine = engine
        self.strategy = strategy
        self._is_running = True
        
    def run(self):
        time.sleep(0.5)
        if self._is_running:
            move, reason = self.engine.solve_next_step(self.strategy)
            self.finished.emit(move, reason, self.engine.nodes_visited)

    def stop(self):
        self._is_running = False

class ProgressBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(6)
        self.progress = 0.0

    def set_progress(self, val):
        self.progress = val
        self.repaint()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        qp.fillRect(0, 0, w, h, QColor("#E0E0E0"))
        fill_w = int(w * self.progress)
        qp.fillRect(0, 0, fill_w, h, QColor("#111111"))

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
        font_main = QFont("Segoe UI", 16, QFont.Weight.Bold)
        qp.setFont(font_main)
        
        if self.victory_mode:
            qp.fillRect(self.rect(), QColor("#FFD700")) 
        
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                x, y = c * self.cell_sz, r * self.cell_sz
                
                bg = QColor("#FFFFFF")
                if self.victory_mode:
                    bg = QColor(255, 255, 255, 60)
                elif self.flash_active and (cell == self.selected_node or self.selected_node):
                    bg = QColor("#FFCCCC")
                elif cell == self.selected_node:
                    bg = QColor("#EEEEEE")
                
                qp.fillRect(x, y, self.cell_sz, self.cell_sz, bg)
                if not self.victory_mode:
                    qp.setPen(QColor("#F0F0F0"))
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
                                
                                rect_x = min(x1, x2) + 6
                                rect_y = min(y1, y2) + 6
                                rect_w = abs(x1 - x2) + self.cell_sz - 12
                                rect_h = abs(y1 - y2) + self.cell_sz - 12
                                
                                color = QColor("#222") if cell.owner_id == 1 else QColor("#888")
                                qp.setBrush(QBrush(color))
                                qp.setPen(Qt.PenStyle.NoPen)
                                qp.drawRoundedRect(QRectF(rect_x, rect_y, rect_w, rect_h), 14.0, 14.0)

        if self.hint_edge:
            n1, n2 = self.hint_edge.node_a, self.hint_edge.node_b
            x1, y1 = n1.c * self.cell_sz + self.cell_sz/2, n1.r * self.cell_sz + self.cell_sz/2
            x2, y2 = n2.c * self.cell_sz + self.cell_sz/2, n2.r * self.cell_sz + self.cell_sz/2
            
            pen = QPen(QColor(180, 180, 180, 180)); pen.setWidth(40); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            qp.setPen(pen)
            qp.drawLine(int(x1), int(y1), int(x2), int(y2))

        for r in range(self.board.rows):
            for c in range(self.board.cols):
                cell = self.board.cells[r][c]
                x, y = c * self.cell_sz, r * self.cell_sz
                
                fg = QColor("#000000")
                if cell.occupied: fg = QColor("#FFFFFF")
                
                qp.setPen(fg)
                qp.drawText(x, y, self.cell_sz, self.cell_sz, Qt.AlignmentFlag.AlignCenter, str(cell.value))

class GameScreen(QWidget):
    def __init__(self, parent, mode):
        super().__init__()
        self.parent = parent
        self.mode = mode 
        
        self.board = DominosaBoard(GRID_HARD)
        self.engine_1 = SolverEngine(self.board)
        self.engine_2 = SolverEngine(self.board)
        
        self.current_turn = 1 
        self.game_over = False
        self.worker = None 
        
        self.status_timer = QTimer()
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(lambda: self.lbl_status.setText("YOUR TURN"))
        
        self.init_ui()
        
        if mode == "DUEL":
            self.timer_duel = QTimer()
            self.timer_duel.timeout.connect(self.run_ai_turn)

    def cleanup(self):
        if self.status_timer.isActive(): self.status_timer.stop()
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        if self.mode == "DUEL": self.timer_duel.stop()

    def init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        
        self.prog_bar = ProgressBar()
        main_lay.addWidget(self.prog_bar)
        
        top_ctrl = QHBoxLayout()
        top_ctrl.setContentsMargins(30, 15, 30, 15)
        
        btn_back = QPushButton("EXIT SESSION")
        btn_back.clicked.connect(lambda: self.parent.switch_to_landing())
        
        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        
        top_ctrl.addWidget(btn_back)
        top_ctrl.addStretch()
        top_ctrl.addWidget(self.lbl_status)
        top_ctrl.addStretch()
        dummy = QPushButton(""); dummy.setFixedWidth(140); dummy.setVisible(False)
        top_ctrl.addWidget(dummy)
        main_lay.addLayout(top_ctrl)
        
        cols_lay = QHBoxLayout()
        cols_lay.setContentsMargins(50, 20, 50, 50)
        
        self.av1 = AvatarWidget("DYNAMIC_PROGRAMMING", "#222222")
        self.av2 = AvatarWidget("DYNAMIC_PROGRAMMING", "#888888")
        if self.mode == "SOLO": 
            self.av1.setVisible(False)
            self.av2.setVisible(False)
        
        left_col = QVBoxLayout()
        if self.mode != "SOLO":
            lbl_p1 = QLabel("PLAYER 1" if self.mode == "VERSUS" else "ALGORITHM A")
            lbl_p1.setObjectName("Subtitle")
            left_col.addWidget(lbl_p1, alignment=Qt.AlignmentFlag.AlignHCenter)
            if self.mode == "DUEL":
                self.combo_algo_1 = QComboBox()
                self.combo_algo_1.addItems(STRATEGIES)
                self.combo_algo_1.currentTextChanged.connect(lambda s: self.av1.set_strategy(s, "#222222"))
                left_col.addWidget(self.combo_algo_1)
        
        if self.mode == "SOLO":
            self.lbl_status.setText("YOUR TURN")
            hint_box = QVBoxLayout()
            lbl_help = QLabel("STRATEGY ENGINE"); lbl_help.setObjectName("Subtitle")
            hint_box.addWidget(lbl_help, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.combo_hint = QComboBox(); self.combo_hint.addItems(STRATEGIES)
            hint_box.addWidget(self.combo_hint)
            btn_hint = QPushButton("GET HINT"); btn_hint.setObjectName("ActionBtn")
            btn_hint.clicked.connect(self.get_hint)
            hint_box.addWidget(btn_hint)
            left_col.addLayout(hint_box)
            
        left_col.addStretch()
        cols_lay.addLayout(left_col, 1)
        
        center_col = QVBoxLayout()
        if self.mode != "SOLO":
            avatars_lay = QHBoxLayout()
            avatars_lay.addStretch()
            avatars_lay.addWidget(self.av1)
            avatars_lay.addSpacing(60)
            avatars_lay.addWidget(self.av2)
            avatars_lay.addStretch()
            center_col.addLayout(avatars_lay)
            center_col.addSpacing(20)

        self.board_wid = BoardWidget(self.board)
        self.board_wid.move_made.connect(self.handle_human_move)
        self.board_wid.board_changed.connect(self.update_progress)
        center_col.addWidget(self.board_wid, alignment=Qt.AlignmentFlag.AlignCenter)
        cols_lay.addLayout(center_col, 3)
        
        right_col = QVBoxLayout()
        if self.mode != "SOLO":
            lbl_p2 = QLabel("PLAYER 2 (CPU)" if self.mode == "VERSUS" else "ALGORITHM B")
            lbl_p2.setObjectName("Subtitle")
            right_col.addWidget(lbl_p2, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.combo_algo_2 = QComboBox(); self.combo_algo_2.addItems(STRATEGIES)
            self.combo_algo_2.currentTextChanged.connect(lambda s: self.av2.set_strategy(s, "#888888"))
            right_col.addWidget(self.combo_algo_2)
            if self.mode == "DUEL":
                right_col.addSpacing(30)
                self.btn_start = QPushButton("START DUEL"); self.btn_start.setObjectName("ActionBtn")
                self.btn_start.clicked.connect(self.start_duel)
                right_col.addWidget(self.btn_start)
        
        right_col.addStretch()
        cols_lay.addLayout(right_col, 1)
        main_lay.addLayout(cols_lay)

    def get_hint(self):
        strat = self.combo_hint.currentText()
        self.lbl_status.setText("ANALYZING...")
        QApplication.processEvents()
        
        move = self.engine_1.get_hint_move(strat)
        if move:
            self.lbl_status.setText("HINT FOUND")
            self.board_wid.show_hint(move)
            self.status_timer.start(2000)
        else:
            self.lbl_status.setText("PUZZLE BLOCKED (Backtrack Required)")

    def update_progress(self):
        val = self.board.get_progress()
        self.prog_bar.set_progress(val)

    def handle_human_move(self, edge):
        if self.game_over: return
        
        success = self.board.confirm_edge(edge, self.current_turn)
        if success:
            self.update_progress()
            self.check_win_condition()
            
            if not self.game_over and self.mode != "SOLO":
                self.current_turn = 2
                self.update_turn_state()

    def start_duel(self):
        self.btn_start.setEnabled(False)
        self.combo_algo_1.setEnabled(False)
        self.combo_algo_2.setEnabled(False)
        self.current_turn = 1
        self.run_ai_turn()

    def update_turn_state(self):
        if self.current_turn == 1:
            self.lbl_status.setText("PLAYER 1 TURN")
            self.av1.set_state("THINKING"); self.av2.set_state("IDLE")
            self.board_wid.input_enabled = (self.mode != "DUEL")
        else:
            self.lbl_status.setText("PLAYER 2 TURN")
            self.av1.set_state("IDLE"); self.av2.set_state("THINKING")
            self.board_wid.input_enabled = False
            self.run_ai_turn()

    def run_ai_turn(self):
        if self.game_over: return
        
        engine = self.engine_1 if self.current_turn == 1 else self.engine_2
        strat_name = "DYNAMIC_PROGRAMMING"
        if self.mode == "DUEL":
             strat_name = self.combo_algo_1.currentText() if self.current_turn == 1 else self.combo_algo_2.currentText()
        else:
             strat_name = self.combo_algo_2.currentText()
        
        if self.worker and self.worker.isRunning():
            self.worker.wait()
            
        self.worker = StrategyWorker(engine, strat_name)
        self.worker.finished.connect(self.on_ai_complete)
        self.worker.start()

    def on_ai_complete(self, move, reason, nodes):
        if self.game_over: return
        
        if move:
            self.board.confirm_edge(move, self.current_turn)
            self.board_wid.repaint()
            self.update_progress()
            self.check_win_condition()
            
            if not self.game_over:
                if self.current_turn == 1: self.av1.set_state("IDLE")
                else: self.av2.set_state("IDLE")
                
                self.current_turn = 1 if self.current_turn == 2 else 2
                if self.mode == "DUEL":
                    self.timer_duel.start(100) 
                else:
                    self.update_turn_state()
        else:
            self.game_over = True
            
            winner_name = ""
            if self.current_turn == 1:
                winner_name = self.combo_algo_2.currentText() if self.mode != "SOLO" else "CPU"
                self.av1.set_state("DEFEAT"); self.av2.set_state("VICTORY")
            else:
                winner_name = self.combo_algo_1.currentText() if self.mode == "DUEL" else "PLAYER 1"
                self.av2.set_state("DEFEAT"); self.av1.set_state("VICTORY")

            self.lbl_status.setText(f"VICTORY: {winner_name} WINS")
            self.board_wid.set_victory(True)

    def check_win_condition(self):
        if self.mode == "SOLO":
            if self.board.get_progress() >= 1.0:
                self.lbl_status.setText("PUZZLE SOLVED")
                self.game_over = True
                self.board_wid.set_victory(True)
        else:
            if not self.board.has_valid_moves():
                self.game_over = True
                self.board_wid.set_victory(True)
                if self.mode == "DUEL": self.timer_duel.stop()
                
                winner_name = ""
                if self.current_turn == 1:
                    winner_name = self.combo_algo_2.currentText() if self.mode != "SOLO" else "CPU"
                    self.av1.set_state("DEFEAT")
                    self.av2.set_state("VICTORY")
                else:
                    winner_name = self.combo_algo_1.currentText() if self.mode == "DUEL" else "PLAYER 1"
                    self.av2.set_state("DEFEAT")
                    self.av1.set_state("VICTORY")
                
                self.lbl_status.setText(f"VICTORY: {winner_name} WINS")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DOMINOSA STRATEGY ENGINE")
        self.resize(1280, 850)
        self.setStyleSheet(STYLES)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.create_landing()

    def create_landing(self):
        landing = QWidget()
        lay = QVBoxLayout(landing)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(30)
        
        title = QLabel("DOMINOSA"); title.setObjectName("Title")
        
        lay.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addSpacing(20)
        
        btn_solo = QPushButton("SOLO PUZZLE"); btn_solo.clicked.connect(lambda: self.launch("SOLO"))
        btn_vs = QPushButton("HUMAN VS ALGO"); btn_vs.clicked.connect(lambda: self.launch("VERSUS"))
        btn_duel = QPushButton("ALGO VS ALGO"); btn_duel.clicked.connect(lambda: self.launch("DUEL"))
        
        lay.addWidget(btn_solo); lay.addWidget(btn_vs); lay.addWidget(btn_duel)
        self.stack.addWidget(landing)

    def launch(self, mode):
        game = GameScreen(self, mode)
        self.stack.addWidget(game)
        self.stack.setCurrentWidget(game)

    def switch_to_landing(self):
        current = self.stack.currentWidget()
        if isinstance(current, GameScreen):
            current.cleanup()
            self.stack.removeWidget(current)
            current.deleteLater()
        self.stack.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())
