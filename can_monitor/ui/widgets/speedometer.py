import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QFont
)


class SpeedometerWidget(QWidget):
    """
    Reusable speedometer widget.

    Parameters
    ----------
    min_val   : minimum value on the gauge
    max_val   : maximum value on the gauge
    """

    def __init__(
        self,
        min_val=0,
        max_val=140,
        parent=None,
    ):
        super().__init__(parent)
        self.max_val = max_val
        self.min_val = min_val
        self._value = min_val
        self.unit = "MPH"
        self.setMinimumSize(280, 280)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_value(self, value: float):
        self._value = max(self.min_val, min(self.max_val, value))
        self.update()  # triggers repaint

    def value(self) -> float:
        return self._value

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        painter.setViewport(
            (self.width() - side) // 2,
            (self.height() - side) // 2,
            side,
            side,
        )
        painter.setWindow(-100, -100, 200, 200)

        self._draw_background(painter)
        self._draw_arc(painter)
        self._draw_ticks(painter)
        self._draw_labels(painter)
        self._draw_unit(painter)
        self._draw_needle(painter)
        self._draw_center_cap(painter)

    def _draw_background(self, painter):
        # Outer bezel
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#1a1a1a"))
        painter.drawEllipse(-100, -100, 200, 200)

        # Inner face
        painter.setBrush(QColor("#111111"))
        painter.drawEllipse(-88, -88, 176, 176)

    def _draw_arc(self, painter):
        """Colored arc around the dial edge."""
        pen = QPen()
        pen.setWidthF(4)
        pen.setCapStyle(Qt.RoundCap)

        start_angle = 225   # degrees (Qt: counter-clockwise from 3 o'clock)
        span = 270          # total sweep

        pen.setColor(QColor("#ffffff"))
        painter.setPen(pen)
        painter.drawArc(-78, -78, 156, 156,
                        start_angle * 16,
                        -int(span * 16))

    def _draw_ticks(self, painter):
        num_major = 7
        num_minor = 3  # minor ticks between each major

        total_ticks = num_major * num_minor + num_major

        for i in range(total_ticks + 1):
            frac = i / total_ticks
            angle = math.radians(225 - frac * 270)

            is_major = (i % (num_minor + 1) == 0)

            if is_major:
                inner_r, outer_r = 62, 76
                width = 1.5
            else:
                inner_r, outer_r = 68, 76
                width = 0.8

            color = QColor("#ffffff")

            pen = QPen(color)
            pen.setWidthF(width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            x1 = inner_r * math.cos(angle)
            y1 = -inner_r * math.sin(angle)
            x2 = outer_r * math.cos(angle)
            y2 = -outer_r * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw_labels(self, painter):
        num_major = 7
        font = QFont("Courier New", 7, QFont.Bold)
        painter.setFont(font)

        for i in range(num_major + 1):
            frac = i / num_major
            val = int(self.min_val + frac * (self.max_val - self.min_val))
            angle = math.radians(225 - frac * 270)

            r = 48
            x = r * math.cos(angle)
            y = -r * math.sin(angle)

            color = QColor("#cccccc")

            painter.setPen(QPen(color))

            label = str(val // 1000) if self.max_val >= 1000 else str(val)
            painter.drawText(
                QPointF(x - 5, y + 4),
                label
            )

    def _draw_unit(self, painter):
        painter.setPen(QColor("#E8A020"))
        font = QFont("Courier New", 6, QFont.Bold)
        painter.setFont(font)
        painter.drawText(-20, 55, 40, 12, Qt.AlignCenter, self.unit)


    def _draw_needle(self, painter):
        frac = (self._value - self.min_val) / (self.max_val - self.min_val)
        angle = math.radians(225 - frac * 270)

        # Needle color — orange like the reference image
        needle_color = QColor("#E8A020")

        # Needle body
        pen = QPen(needle_color)
        pen.setWidthF(2.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        tip_r = 70
        tail_r = 12

        tx = tip_r * math.cos(angle)
        ty = -tip_r * math.sin(angle)
        bx = -tail_r * math.cos(angle)
        by = tail_r * math.sin(angle)

        painter.drawLine(QPointF(bx, by), QPointF(tx, ty))

        # Small counterweight bump at tail
        pen.setWidthF(3.5)
        painter.setPen(pen)
        painter.drawLine(QPointF(bx, by), QPointF(bx * 0.5, by * 0.5))

    def _draw_center_cap(self, painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#333333"))
        painter.drawEllipse(-6, -6, 12, 12)
        painter.setBrush(QColor("#E8A020"))
        painter.drawEllipse(-3, -3, 6, 6)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _value_to_angle_span(self, value) -> float:
        """Convert a value to degrees swept from the start of the arc."""
        frac = (value - self.min_val) / (self.max_val - self.min_val)
        return frac * 270


# ── Demo window ───────────────────────────────────────────────────────────────

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gauge Demo")
        self.setStyleSheet("background-color: #0d0d0d;")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        self.gauge = SpeedometerWidget(
            min_val=0,
            max_val=140
        )
        layout.addWidget(self.gauge)
        self.setLayout(layout)

        # Animate needle for demo
        self._demo_value = 0
        self._direction = 1
        timer = QTimer(self)
        timer.timeout.connect(self._animate)
        timer.start(60)

    def _animate(self):
        self._demo_value += 5 * self._direction
        if self._demo_value >= 140:
            self._direction = -1
        elif self._demo_value <= 0:
            self._direction = 1
        self.gauge.set_value(self._demo_value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DemoWindow()
    win.resize(320, 320)
    win.show()
    sys.exit(app.exec_())
