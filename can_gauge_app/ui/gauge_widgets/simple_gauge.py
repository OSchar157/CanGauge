import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QFont
)

from ui.gauge_widgets.gauge import Gauge, ParamSpec

# TODO: Allow advanced customization: color schemes, arc start/end positions, number of ticks, etc


ARC_START = 225   # degrees (Qt: counter-clockwise from 3 o'clock)
ARC_SPAN = 270    # total sweep
ARC_END = ARC_START - ARC_SPAN

WARNING_ZONE_COLOR = "#E8A020"
DANGER_ZONE_COLOR = "#CC2200"
SAFE_ZONE_COLOR = "#ffffff"

NUM_MAJOR_TICKS = 10
NUM_MINOR_TICKS = 3

class SimpleGauge(Gauge):
    """
    Reusable gauge widget.

    args:
        min_val         (float):    minimum value on the gauge
        max_val         (float):    maximum value on the gauge
        warn_low        (float):    value where low warning zone ends
        warn_high        (float):    value where high warning zone begins
        danger_low      (float):    value where low danger zone ends
        danger_high     (float):    value where high danger zone begins
        untit           (str):      units of the value
    """

    name = "Simple Gauge"
    
    def __init__(
        self,
        min_val=0,
        max_val=100,
        warn_low=20,
        warn_high=80,
        danger_low=10,
        danger_high=90,
        unit="",
        label="",
        parent=None
    ):
        super().__init__(
            min_val,
            max_val,
            warn_low,
            warn_high,
            danger_low,
            danger_high,
            unit,
            label,
            parent
        )

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

    def _draw_background(self, painter: QPainter):
        # Outer bezel
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#1a1a1a"))
        painter.drawEllipse(-100, -100, 200, 200)

        # Inner face
        painter.setBrush(QColor("#111111"))
        painter.drawEllipse(-88, -88, 176, 176)

    def _draw_arc(self, painter: QPainter):
        """Colored arc around the dial edge."""
        pen = QPen()
        pen.setWidthF(4)
        pen.setCapStyle(Qt.RoundCap)

        ang_start = ARC_START
        ang_danger_low = ARC_START - self._value_to_angle_span(self.danger_low) if self.danger_low else ang_start
        ang_warn_low   = ARC_START - self._value_to_angle_span(self.warn_low)   if self.warn_low   else ang_danger_low
        
        ang_warn_high  = ARC_START - self._value_to_angle_span(self.warn_high)  if self.warn_high  else ARC_END
        ang_danger_high= ARC_START - self._value_to_angle_span(self.danger_high) if self.danger_high else ang_warn_high
        ang_end   = ARC_END

        # Low Danger Zone (Red)
        self._draw_segment(painter, pen, ang_start, ang_danger_low, DANGER_ZONE_COLOR)

        # Low Warning Zone (Orange)
        self._draw_segment(painter, pen, ang_danger_low, ang_warn_low, WARNING_ZONE_COLOR)

        # Normal Zone (White)
        self._draw_segment(painter, pen, ang_warn_low, ang_warn_high, SAFE_ZONE_COLOR)

        # High Warning Zone (Orange)
        self._draw_segment(painter, pen, ang_warn_high, ang_danger_high, WARNING_ZONE_COLOR)

        # High Danger Zone (Red)
        self._draw_segment(painter, pen, ang_danger_high, ang_end, DANGER_ZONE_COLOR)

    def _draw_ticks(self, painter):
        total_ticks = NUM_MAJOR_TICKS * NUM_MINOR_TICKS + NUM_MAJOR_TICKS
        middle_minor = (NUM_MINOR_TICKS + 1) // 2  # index within group that is middle

        for i in range(total_ticks + 1):
            frac = i / total_ticks
            angle = math.radians(225 - frac * 270)

            is_major = (i % (NUM_MINOR_TICKS + 1) == 0)
            position_in_group = i % (NUM_MINOR_TICKS + 1)
            is_middle_minor = (not is_major) and (NUM_MINOR_TICKS % 2 == 1) and (position_in_group == middle_minor)

            if is_major:
                inner_r, outer_r = 62, 76
                width = 1.5
            elif is_middle_minor:
                inner_r, outer_r = 65, 76  # slightly longer than regular minor
                width = 1.1
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

        font = QFont("Courier New", 7, QFont.Bold)
        painter.setFont(font)

        for i in range(NUM_MAJOR_TICKS + 1):
            frac = i / NUM_MAJOR_TICKS
            val = int(self.min_val + frac * (self.max_val - self.min_val))
            angle = math.radians(225 - frac * 270)

            r = 48
            x = r * math.cos(angle)
            y = -r * math.sin(angle)

            color = QColor("#cccccc")

            painter.setPen(QPen(color))

            # label = str(val // 1000) if self.max_val >= 1000 else str(val)
            label = str(val)
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
        return frac * ARC_SPAN
    
    def _draw_segment(self, painter, pen, start_ang, end_ang, color_hex):
        if start_ang == end_ang:
            return # Skip if zone doesn't exist
        span = end_ang - start_ang # Naturally negative because it's clockwise
        pen.setColor(QColor(color_hex))
        painter.setPen(pen)
        painter.drawArc(-78, -78, 156, 156, int(start_ang * 16), int(span * 16))

# ── Demo window ───────────────────────────────────────────────────────────────

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gauge Demo")
        self.setStyleSheet("background-color: #0d0d0d;")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        self.gauge = SimpleGauge()
        layout.addWidget(self.gauge)
        self.setLayout(layout)

        # Animate needle for demo
        self._demo_value = 0
        self._direction = 1
        timer = QTimer(self)
        timer.timeout.connect(self._animate)
        timer.start(20)

    def _animate(self):
        self._demo_value += 1 * self._direction
        if self._demo_value >= 100:
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
