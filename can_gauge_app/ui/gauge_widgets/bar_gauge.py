import sys
import math
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient

from ui.gauge_widgets.gauge import Gauge, ParamSpec

WARNING_COLOR  = QColor("#E8A020")
DANGER_COLOR   = QColor("#CC2200")
SAFE_COLOR     = QColor("#1D9E75")
EMPTY_COLOR    = QColor("#2a2a2a")
TICK_COLOR     = QColor("#555555")
LABEL_COLOR    = QColor("#aaaaaa")
UNIT_COLOR     = QColor("#E8A020")

NUM_TICKS = 5          # Number of tick marks on the side scale
SEGMENT_GAP = 3        # px gap between bar segments
NUM_SEGMENTS = 100      # Total stacked segments

# TODO: create better the value updates to have 'confidency zones' so that the gauge doesnt flicker when value is on the edge

class BarGauge(Gauge):
    """
    Reusable vertical bar-graph gauge.

    args:
        min_val         (float):    minimum value on the gauge
        max_val         (float):    maximum value on the gauge
        warn_low        (float):    value where low warning zone ends
        warn_high       (float):    value where high warning zone begins
        danger_low      (float):    value where low danger zone ends
        danger_high     (float):    value where high danger zone begins
        untit           (str):      units of the value
        label           (str):      optional text field
    """
    name = "Bar Gauge"
    
    def __init__(self,
                 min_val=0,
                 max_val=100,
                 warn_low=20,
                 warn_high=None,
                 danger_low=10,
                 danger_high=None,
                 unit="%",
                 label="Gas",
                 parent=None
            ):
        
        super().__init__(min_val, max_val, warn_low,
                        warn_high, danger_low, danger_high,
                        unit, label, parent)

    def to_json(self):
        return super().to_json()
    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()

        # Layout zones
        label_h   = 22
        value_h   = 28
        unit_h    = 18
        tick_w    = 28    # side tick + label column
        bar_margin_top    = label_h + 8
        bar_margin_bottom = value_h + unit_h + 8
        bar_x     = tick_w
        bar_w     = W - tick_w - 10
        bar_y     = bar_margin_top
        bar_h     = H - bar_margin_top - bar_margin_bottom

        self._draw_label(painter, W, label_h)
        self._draw_bar(painter, bar_x, bar_y, bar_w, bar_h)
        self._draw_ticks(painter, tick_w, bar_y, bar_h)
        self._draw_value(painter, W, H - bar_margin_bottom + 6, value_h, unit_h)

    def _draw_label(self, painter, W, label_h):
        if not self.label:
            return
        font = QFont("Courier New", 8, QFont.Bold)
        painter.setFont(font)
        painter.setPen(LABEL_COLOR)
        painter.drawText(0, 0, W, label_h, Qt.AlignCenter, self.label)

    def _draw_bar(self, painter, bx, by, bw, bh):
        """Draw segmented bar fill with zone-aware coloring."""
        seg_total_h = (bh - SEGMENT_GAP * (NUM_SEGMENTS - 1)) / NUM_SEGMENTS
        seg_h = max(2, seg_total_h)
        radius = seg_h * 0.45

        frac = (self._value - self.min_val) / max(1, self.max_val - self.min_val)
        filled = int(round(frac * NUM_SEGMENTS))

        for i in range(NUM_SEGMENTS):
            # i=0 is bottom segment
            seg_frac = i / NUM_SEGMENTS          # value fraction this segment represents
            seg_val  = self.min_val + seg_frac * (self.max_val - self.min_val)

            y = by + bh - (i + 1) * seg_h - i * SEGMENT_GAP

            if i < filled:
                color = self._zone_color(seg_val)
            else:
                color = EMPTY_COLOR

            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            rect = QRectF(bx, y, bw, seg_h)
            painter.drawRoundedRect(rect, radius, radius)

    def _draw_ticks(self, painter, tick_w, by, bh):
        """Draw scale ticks and labels on the left."""
        font = QFont("Courier New", 7)
        painter.setFont(font)

        for i in range(NUM_TICKS + 1):
            frac = i / NUM_TICKS
            val  = self.min_val + frac * (self.max_val - self.min_val)
            y    = by + bh - frac * bh

            # Tick line
            pen = QPen(TICK_COLOR)
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(tick_w - 6, int(y), tick_w - 1, int(y))

            # Label
            painter.setPen(LABEL_COLOR)
            label = str(int(round(val)))
            painter.drawText(0, int(y) - 7, tick_w - 8, 14, Qt.AlignRight | Qt.AlignVCenter, label)

    def _draw_value(self, painter, W, y, value_h, unit_h):
        """Draw the numeric readout and unit below the bar."""
        # Numeric value
        font = QFont("Courier New", 13, QFont.Bold)
        painter.setFont(font)
        color = self._zone_color(self._value)
        painter.setPen(color)
        val_text = f"{self._value:.0f}"
        painter.drawText(0, y, W, value_h, Qt.AlignCenter, val_text)

        # Unit
        font2 = QFont("Courier New", 7, QFont.Bold)
        painter.setFont(font2)
        painter.setPen(UNIT_COLOR)
        painter.drawText(0, y + value_h - 2, W, unit_h, Qt.AlignCenter, self.unit)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _zone_color(self, val) -> QColor:
        if self.danger_high is not None and val >= self.danger_high:
            return DANGER_COLOR
        if self.warn_high is not None and val >= self.warn_high:
            return WARNING_COLOR
        if self.danger_low is not None and val <= self.danger_low:
            return DANGER_COLOR
        if self.warn_low is not None and val <= self.warn_low:
            return WARNING_COLOR
        return SAFE_COLOR


# ── Demo window ───────────────────────────────────────────────────────────────

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bar Gauge Demo")
        self.setStyleSheet("background-color: #0d0d0d;")

        layout = QHBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self.battery = BarGauge(
            min_val=0, max_val=100,
            danger_low=10, warn_low=20,
            warn_high=None, danger_high=None,
            unit="%", label="BATTERY",
        )

        self.fuel = BarGauge(
            min_val=0, max_val=100,
            danger_low=10, warn_low=25,
            warn_high=None, danger_high=None,
            unit="L", label="FUEL",
        )

        self.temp = BarGauge(
            min_val=0, max_val=120,
            danger_low=None, warn_low=None,
            warn_high=85, danger_high=100,
            unit="°C", label="TEMP",
        )

        for g in (self.battery, self.fuel, self.temp):
            layout.addWidget(g)

        self.setLayout(layout)

        self._t = 0
        timer = QTimer(self)
        timer.timeout.connect(self._animate)
        timer.start(30)

    def _animate(self):
        self._t += 1
        # Battery drains slowly
        batt = 100 - (self._t % 200) * 0.5
        self.battery.set_value(batt)

        # Fuel oscillates
        fuel = 50 + 45 * math.sin(self._t * 0.02)
        self.fuel.set_value(fuel)

        # Temperature rises then cools
        temp = 60 + 55 * abs(math.sin(self._t * 0.015))
        self.temp.set_value(temp)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DemoWindow()
    win.resize(360, 320)
    win.show()
    sys.exit(app.exec_())