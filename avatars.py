from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QPainter, QBrush, QPainterPath, QPen

class AvatarWidget(QWidget):
    def __init__(self, strategy="DYNAMIC_PROGRAMMING", color="#000000"):
        super().__init__()
        self.setFixedSize(80, 80)
        self.strategy = strategy
        self.base_color = QColor(color)
        self.state = "IDLE"
        self.blink_frame = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

    def set_strategy(self, strat, color):
        self.strategy = strat
        self.base_color = QColor(color)
        self.repaint()

    def set_state(self, new_state):
        self.state = new_state
        self.repaint()

    def animate(self):
        if self.state == "THINKING":
            self.blink_frame += 1
            self.repaint()
        elif self.blink_frame != 0:
            self.blink_frame = 0
            self.repaint()

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_col = self.base_color
        fg_col = QColor("#FFFFFF")
        
        if self.state == "VICTORY":
            bg_col = QColor("#FFD700")
            fg_col = QColor("#000000")
        elif self.state == "DEFEAT":
            bg_col = QColor("#555555")
            fg_col = QColor("#AAAAAA")

        qp.setBrush(QBrush(bg_col))
        qp.setPen(Qt.PenStyle.NoPen)
        
        size = 60
        offset = 10
        
        if self.strategy == "DYNAMIC_PROGRAMMING":
            qp.drawRoundedRect(offset, offset, size, size, 8.0, 8.0)
        elif self.strategy == "GREEDY":
            qp.drawEllipse(offset, offset, size, size)
        elif self.strategy == "DIVIDE_CONQUER":
            path = QPainterPath()
            path.moveTo(40, 10)
            path.lineTo(70, 70)
            path.lineTo(10, 70)
            path.closeSubpath()
            qp.drawPath(path)
        else:
            qp.drawRect(offset, offset, size, size)
        
        qp.setPen(QPen(fg_col, 3))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        
        eye_y = 35
        left_x, right_x = 25, 45
        if self.strategy == "DIVIDE_CONQUER":
            eye_y = 45
            left_x, right_x = 30, 42

        if self.state == "VICTORY":
            path_l = QPainterPath()
            path_l.moveTo(left_x - 5, eye_y + 3)
            path_l.lineTo(left_x, eye_y - 3)
            path_l.lineTo(left_x + 5, eye_y + 3)
            qp.drawPath(path_l)

            path_r = QPainterPath()
            path_r.moveTo(right_x - 5, eye_y + 3)
            path_r.lineTo(right_x, eye_y - 3)
            path_r.lineTo(right_x + 5, eye_y + 3)
            qp.drawPath(path_r)
            
        elif self.state == "DEFEAT":
            qp.drawLine(left_x - 3, eye_y - 3, left_x + 3, eye_y + 3)
            qp.drawLine(left_x + 3, eye_y - 3, left_x - 3, eye_y + 3)
            qp.drawLine(right_x - 3, eye_y - 3, right_x + 3, eye_y + 3)
            qp.drawLine(right_x + 3, eye_y - 3, right_x - 3, eye_y + 3)
            
        else:
            if self.state == "THINKING":
                shift = (self.blink_frame // 2 % 6) - 3
                left_x += shift
                right_x += shift
                
            qp.setBrush(QBrush(fg_col))
            qp.setPen(Qt.PenStyle.NoPen)
            qp.drawRect(left_x - 3, eye_y - 3, 6, 6)
            qp.drawRect(right_x - 3, eye_y - 3, 6, 6)
        
        mouth_pen = QPen(fg_col, 3)
        mouth_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        qp.setPen(mouth_pen)
        qp.setBrush(Qt.BrushStyle.NoBrush)
        
        mouth_y = 55
        if self.strategy == "DIVIDE_CONQUER":
            mouth_y = 62
        
        if self.state == "VICTORY":
            rect = QRectF(30, mouth_y - 10, 20, 20)
            qp.drawArc(rect, 180 * 16, 180 * 16)
            
        elif self.state == "DEFEAT":
            path = QPainterPath()
            path.moveTo(30, mouth_y + 5)
            path.quadTo(40, mouth_y - 5, 50, mouth_y + 5)
            qp.drawPath(path)
            
        elif self.state == "THINKING":
            width = 10 + (self.blink_frame % 8) * 2
            qp.drawLine(40 - width//2, mouth_y, 40 + width//2, mouth_y)
            
        else:
            qp.drawLine(35, mouth_y, 45, mouth_y)
