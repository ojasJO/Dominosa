from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QPainter, QBrush, QPainterPath, QPen


class AvatarWidget(QWidget):
    def __init__(self, strategy="BACKTRACKING", color="#000000"):
        super().__init__()
        self.setFixedSize(80, 80)
        self.strategy = strategy
        self.base_color = QColor(color)
        self.state = "IDLE"
        self.blink_frame = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)

    def set_strategy(self, strat, color):
        self.strategy = strat
        self.base_color = QColor(color)
        self.repaint()

    def set_state(self, new_state):
        self.state = new_state
        self.repaint()

    def _animate(self):
        if self.state == "THINKING":
            self.blink_frame += 1
            self.repaint()
        elif self.blink_frame != 0:
            self.blink_frame = 0
            self.repaint()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = self.base_color
        fg = QColor("#FFFFFF")

        if self.state == "VICTORY":
            bg = QColor("#FFD700")
            fg = QColor("#000000")
        elif self.state == "DEFEAT":
            bg = QColor("#555555")
            fg = QColor("#AAAAAA")

        qp.setBrush(QBrush(bg))
        qp.setPen(Qt.PenStyle.NoPen)

        # ── Body shape per strategy ────────────────────────────────────
        if self.strategy == "GREEDY":
            # Circle — simple, fast
            qp.drawEllipse(10, 10, 60, 60)
            eye_y, lx, rx = 35, 25, 45
            mouth_y = 55

        elif self.strategy == "DIVIDE_CONQUER":
            # Triangle — divide
            path = QPainterPath()
            path.moveTo(40, 10)
            path.lineTo(70, 70)
            path.lineTo(10, 70)
            path.closeSubpath()
            qp.drawPath(path)
            eye_y, lx, rx = 45, 30, 42
            mouth_y = 62

        elif self.strategy == "DYNAMIC_PROGRAMMING":
            # Rounded rect — structured, systematic
            qp.drawRoundedRect(10, 10, 60, 60, 8.0, 8.0)
            eye_y, lx, rx = 35, 25, 45
            mouth_y = 55

        elif self.strategy == "BACKTRACKING":
            # Diamond — branches and backtracks
            path = QPainterPath()
            path.moveTo(40, 6)   # top
            path.lineTo(72, 40)  # right
            path.lineTo(40, 74)  # bottom
            path.lineTo(8,  40)  # left
            path.closeSubpath()
            qp.drawPath(path)
            eye_y, lx, rx = 38, 28, 44
            mouth_y = 56

        else:
            qp.drawRect(10, 10, 60, 60)
            eye_y, lx, rx = 35, 25, 45
            mouth_y = 55

        # ── Eyes ──────────────────────────────────────────────────────
        qp.setPen(QPen(fg, 3))
        qp.setBrush(Qt.BrushStyle.NoBrush)

        if self.state == "VICTORY":
            for x in (lx, rx):
                p = QPainterPath()
                p.moveTo(x - 5, eye_y + 3)
                p.lineTo(x,     eye_y - 3)
                p.lineTo(x + 5, eye_y + 3)
                qp.drawPath(p)

        elif self.state == "DEFEAT":
            for x in (lx, rx):
                qp.drawLine(x - 3, eye_y - 3, x + 3, eye_y + 3)
                qp.drawLine(x + 3, eye_y - 3, x - 3, eye_y + 3)

        else:
            if self.state == "THINKING":
                shift = (self.blink_frame // 2 % 6) - 3
                lx += shift
                rx += shift
            qp.setBrush(QBrush(fg))
            qp.setPen(Qt.PenStyle.NoPen)
            qp.drawRect(lx - 3, eye_y - 3, 6, 6)
            qp.drawRect(rx - 3, eye_y - 3, 6, 6)

        # ── Mouth ─────────────────────────────────────────────────────
        mouth_pen = QPen(fg, 3)
        mouth_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        qp.setPen(mouth_pen)
        qp.setBrush(Qt.BrushStyle.NoBrush)

        if self.state == "VICTORY":
            qp.drawArc(QRectF(30, mouth_y - 10, 20, 20), 180 * 16, 180 * 16)

        elif self.state == "DEFEAT":
            p = QPainterPath()
            p.moveTo(30, mouth_y + 5)
            p.quadTo(40, mouth_y - 5, 50, mouth_y + 5)
            qp.drawPath(p)

        elif self.state == "THINKING":
            w = 10 + (self.blink_frame % 8) * 2
            qp.drawLine(40 - w // 2, mouth_y, 40 + w // 2, mouth_y)

        else:
            qp.drawLine(35, mouth_y, 45, mouth_y)
