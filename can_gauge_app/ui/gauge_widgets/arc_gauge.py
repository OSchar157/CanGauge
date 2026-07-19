import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont

from ui.gauge_widgets.gauge import ParamSpec, Gauge

# Arc geometry — shallow sweep like a real fuel gauge
# Qt angles: 0 = 3 o'clock, counter-clockwise positive
# We want the arc to start bottom-left and end bottom-right
ARC_START  = 150   # degrees from 3 o'clock (bottom-left)
ARC_SPAN   = 120   # total sweep (shallow, not a semicircle)
ARC_END    = ARC_START - ARC_SPAN  # = 90 (bottom-right)

WARNING_COLOR = QColor("#E8A020")
DANGER_COLOR  = QColor("#CC2200")
SAFE_COLOR    = QColor("#ffffff")
BG_OUTER      = QColor("#1a1a1a")
BG_INNER      = QColor("#111111")
NEEDLE_COLOR  = QColor("#E8A020")
LABEL_COLOR   = QColor("#cccccc")
UNIT_COLOR    = QColor("#E8A020")

NUM_MAJOR_TICKS = 8
NUM_MINOR_TICKS = 3


class ArcGauge(Gauge):
    """
    Shallow arc gauge styled after a vehicle fuel/temp gauge.

    Args:
        min_val (float): Minimum value (shown as min_label)
        max_val (float): Maximum value (shown as max_label)
        warn_low (float|None): Start of low warning zone
        warn_high (float|None): Start of high warning zone
        danger_low (float|None): Start of low danger zone
        danger_high (float|None): Start of high danger zone
        label (str): Optional text field
        min_label (str): Label drawn at the min end (default "E")
        max_label (str): Label drawn at the max end (default "F")
        mid_label (str): Label drawn at the midpoint (default "1/2")
        unit (str): Unit string shown below the needle pivot
    """
    name = "Arc Gauge"
    
    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        fields = super().get_fields() + [
            ParamSpec("min_label", "Minimum Label", str),
            ParamSpec("max_label", "Maximum Label", str),
            ParamSpec("mid_label", "Mid Label", str)
        ]
        return fields

    def __init__(
        self,
        min_val=0,
        max_val=100,
        warn_low=20,
        warn_high=80,
        danger_low=10,
        danger_high=90,
        min_label="E",
        max_label="F",
        mid_label="1/2",
        unit="",
        label="",
        parent=None,
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
        self.min_label = min_label
        self.max_label = max_label
        self.mid_label = mid_label
        self.setMinimumSize(280, 180)

    # ── Public API ────────────────────────────────────────────────────────────

    def to_json(self):
        return super().to_json()

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Square viewport centred, shifted up so the arc sits nicely
        # The arc is shallow so we don't need the full square height
        w, h = self.width(), self.height()
        side = min(w, int(h * 1.6))  # wider than tall for a shallow arc
        vx = (w - side) // 2
        vy = (h - side) // 2
        painter.setViewport(vx, vy, side, side)
        painter.setWindow(-100, -100, 200, 200)

        self._draw_background(painter)
        self._draw_arc(painter)
        self._draw_ticks(painter)
        self._draw_end_labels(painter)
        self._draw_mid_label(painter)
        self._draw_unit(painter)
        self._draw_needle(painter)
        self._draw_center_cap(painter)

    def _draw_background(self, painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(BG_OUTER)
        painter.drawEllipse(-100, -100, 200, 200)
        painter.setBrush(BG_INNER)
        painter.drawEllipse(-88, -88, 176, 176)

    def _draw_arc(self, painter):
        pen = QPen()
        pen.setWidthF(4)
        pen.setCapStyle(Qt.RoundCap)

        def span_for(val):
            if val is None:
                return None
            frac = (val - self.min_val) / (self.max_val - self.min_val)
            return frac * ARC_SPAN

        ang_start = ARC_START

        s_dl = span_for(self.danger_low)
        s_wl = span_for(self.warn_low)
        s_wh = span_for(self.warn_high)
        s_dh = span_for(self.danger_high)

        ang_dl = (ARC_START - s_dl) if s_dl is not None else ang_start
        ang_wl = (ARC_START - s_wl) if s_wl is not None else ang_dl
        ang_wh = (ARC_START - s_wh) if s_wh is not None else ARC_END
        ang_dh = (ARC_START - s_dh) if s_dh is not None else ang_wh
        ang_end = ARC_END

        self._draw_segment(painter, pen, ang_start, ang_dl, DANGER_COLOR)
        self._draw_segment(painter, pen, ang_dl,    ang_wl, WARNING_COLOR)
        self._draw_segment(painter, pen, ang_wl,    ang_wh, SAFE_COLOR)
        self._draw_segment(painter, pen, ang_wh,    ang_dh, WARNING_COLOR)
        self._draw_segment(painter, pen, ang_dh,    ang_end, DANGER_COLOR)

    def _draw_ticks(self, painter):
        total = NUM_MAJOR_TICKS * (NUM_MINOR_TICKS + 1)
        middle_minor = (NUM_MINOR_TICKS + 1) // 2

        for i in range(total + 1):
            frac = i / total
            angle = math.radians(ARC_START - frac * ARC_SPAN)

            is_major = (i % (NUM_MINOR_TICKS + 1) == 0)
            pos_in_group = i % (NUM_MINOR_TICKS + 1)
            is_mid_minor = (not is_major) and (NUM_MINOR_TICKS % 2 == 1) and (pos_in_group == middle_minor)

            if is_major:
                inner_r, outer_r, width = 62, 76, 1.5
            elif is_mid_minor:
                inner_r, outer_r, width = 65, 76, 1.1
            else:
                inner_r, outer_r, width = 68, 76, 0.8

            pen = QPen(QColor("#ffffff"))
            pen.setWidthF(width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            x1 = inner_r * math.cos(angle)
            y1 = -inner_r * math.sin(angle)
            x2 = outer_r * math.cos(angle)
            y2 = -outer_r * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    def _draw_end_labels(self, painter):
        """Draw min/max labels (E / F) at the ends of the arc."""
        font = QFont("Courier New", 11, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(LABEL_COLOR))

        for frac, text in [(0.0, self.min_label), (1.0, self.max_label)]:
            angle = math.radians(ARC_START - frac * ARC_SPAN)
            r = 55
            x = r * math.cos(angle)
            y = -r * math.sin(angle)
            painter.drawText(QPointF(x - 6, y + 5), text)

    def _draw_mid_label(self, painter):
        """Draw the midpoint label (1/2) above centre of arc."""
        if not self.mid_label:
            return
        angle = math.radians(ARC_START - 0.5 * ARC_SPAN)
        r = 52
        x = r * math.cos(angle)
        y = -r * math.sin(angle)

        font = QFont("Courier New", 9, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(LABEL_COLOR))
        painter.drawText(QPointF(x - 10, y + 4), self.mid_label)

    def _draw_unit(self, painter):
        if not self.unit:
            return
        painter.setPen(UNIT_COLOR)
        font = QFont("Courier New", 6, QFont.Bold)
        painter.setFont(font)
        painter.drawText(-20, 30, 40, 12, Qt.AlignCenter, self.unit)

    def _draw_needle(self, painter):
        frac = (self._value - self.min_val) / (self.max_val - self.min_val)
        angle = math.radians(ARC_START - frac * ARC_SPAN)

        pen = QPen(NEEDLE_COLOR)
        pen.setWidthF(2.2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        tip_r  = 70
        tail_r = 14

        tx = tip_r * math.cos(angle)
        ty = -tip_r * math.sin(angle)
        bx = -tail_r * math.cos(angle)
        by = tail_r * math.sin(angle)

        painter.drawLine(QPointF(bx, by), QPointF(tx, ty))

        pen.setWidthF(3.5)
        painter.setPen(pen)
        painter.drawLine(QPointF(bx, by), QPointF(bx * 0.5, by * 0.5))

    def _draw_center_cap(self, painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#333333"))
        painter.drawEllipse(-6, -6, 12, 12)
        painter.setBrush(NEEDLE_COLOR)
        painter.drawEllipse(-3, -3, 6, 6)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _draw_segment(self, painter, pen, start_ang, end_ang, color):
        if start_ang == end_ang:
            return
        span = end_ang - start_ang
        pen.setColor(color)
        painter.setPen(pen)
        painter.drawArc(-78, -78, 156, 156, int(start_ang * 16), int(span * 16))


# ── Demo window ───────────────────────────────────────────────────────────────

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arc Gauge Demo")
        self.setStyleSheet("background-color: #0d0d0d;")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        self.gauge = ArcGauge(
            min_val=0, max_val=100,
            danger_low=10, warn_low=20,
            warn_high=80, danger_high=90,
            min_label="E", max_label="F", mid_label="1/2",
            unit="fuel %",
        )
        layout.addWidget(self.gauge)
        self.setLayout(layout)

        self._v = 0
        self._dir = 1
        timer = QTimer(self)
        timer.timeout.connect(self._animate)
        timer.start(20)

    def _animate(self):
        self._v += self._dir
        if self._v >= 100: self._dir = -1
        elif self._v <= 0: self._dir = 1
        self.gauge.set_value(self._v)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DemoWindow()
    win.resize(360, 240)
    win.show()
    sys.exit(app.exec_())