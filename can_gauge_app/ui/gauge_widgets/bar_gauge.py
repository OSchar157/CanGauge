import sys
import math

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QRectF, QSize
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics

from ui.gauge_widgets.gauge import Gauge, ParamSpec

# ── Colors ────────────────────────────────────────────────────────────────────
WARNING_COLOR = QColor("#E8A020")
DANGER_COLOR  = QColor("#CC2200")
SAFE_COLOR    = QColor("#1D9E75")
EMPTY_COLOR   = QColor("#2a2a2a")
TICK_COLOR    = QColor("#555555")
LABEL_COLOR   = QColor("#aaaaaa")
UNIT_COLOR    = QColor("#E8A020")

# ── Layout ────────────────────────────────────────────────────────────────────
MIN_WIDTH  = 200     # width constraints keep the gauge at a sensible size
MIN_HEIGHT = 240

ZONE_PAD      = 8    # vertical padding between label / bar / value zones
TICK_LEN      = 6    # length of the tick marks
TICK_TEXT_PAD = 6    # gap between tick label text and the tick mark

NUM_TICKS    = 5     # number of tick intervals on the side scale
NUM_SEGMENTS = 100   # total stacked segments
SEGMENT_GAP  = 3     # px gap between segments (shrinks automatically if tight)

MAX_NUM_DEC = 3

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_FAMILY     = "Courier New"
LABEL_FONT_SIZE = 16
TICK_FONT_SIZE  = 13
VALUE_FONT_SIZE = 22
UNIT_FONT_SIZE  = 12


class BarGauge(Gauge):

    name = "Bar Gauge"

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        gauge_fields = super().get_fields()
        
        return gauge_fields + [ParamSpec("num_dec_places", "Decimal Places", int, 3)]

    def __init__(
            self,
            val_offset,
            val_scale,
            min_val,
            max_val,
            warn_low,
            warn_high,
            danger_low,
            danger_high,
            unit,
            label,
            num_dec_places: int = 3,
            parent=None
        ):

        super().__init__(
            val_offset, 
            val_scale, 
            min_val, 
            max_val,
            warn_low, 
            warn_high, 
            danger_low, 
            danger_high,
            unit, 
            label,
            parent)

        dec_range = range(MAX_NUM_DEC + 1)
        if num_dec_places not in dec_range:
            raise ValueError(f"num_dec_places must be in {dec_range}")
        
        self.num_dec_places = num_dec_places

        # Keep the gauge from stretching across the whole layout: it may grow
        # vertically, but its width stays within a fixed band.
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._label_font = QFont(FONT_FAMILY, LABEL_FONT_SIZE, QFont.Bold)
        self._tick_font  = QFont(FONT_FAMILY, TICK_FONT_SIZE)
        self._value_font = QFont(FONT_FAMILY, VALUE_FONT_SIZE, QFont.Bold)
        self._unit_font  = QFont(FONT_FAMILY, UNIT_FONT_SIZE, QFont.Bold)

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()

        fm_label = QFontMetrics(self._label_font)
        fm_tick  = QFontMetrics(self._tick_font)
        fm_value = QFontMetrics(self._value_font)
        fm_unit  = QFontMetrics(self._unit_font)

        # Vertical layout: label on top, value + unit at the bottom, bar
        # filling whatever is left in between.
        label_h = fm_label.height() if self.label else 0
        value_h = fm_value.height()
        unit_h  = fm_unit.height()

        bar_y      = label_h + max(ZONE_PAD, fm_tick.height() // 2)
        bar_bottom = H - (value_h + unit_h + ZONE_PAD + 2)
        bar_h      = bar_bottom - bar_y

        # Horizontal layout: the tick column is sized to fit the widest tick
        # label, and is mirrored by an equal empty margin on the right, so the
        # bar sits dead-center in the widget on the same axis as the label,
        # value, and unit text.
        tick_col_w = self._tick_column_width(fm_tick)
        bar_x = tick_col_w
        bar_w = W - 2 * tick_col_w

        self._draw_label(painter, W, label_h)
        if bar_w > 0 and bar_h > 0:
            self._draw_bar(painter, bar_x, bar_y, bar_w, bar_h)
            self._draw_ticks(painter, fm_tick, tick_col_w, bar_y, bar_h)
        self._draw_value(painter, W, bar_bottom + ZONE_PAD, value_h, unit_h)

    def _draw_label(self, painter, W, label_h):
        if not self.label:
            return
        painter.setFont(self._label_font)
        painter.setPen(LABEL_COLOR)
        painter.drawText(0, 0, W, label_h, Qt.AlignCenter, self.label)

    def _draw_bar(self, painter, bx, by, bw, bh):
        """Draw the segmented bar fill with zone-aware coloring (i=0 = bottom).

        Each segment owns an equal slot of the bar height and is drawn centered
        inside it, so segments can never spill outside the bar area no matter
        how many there are or how small the widget gets.
        """
        slot_h = bh / NUM_SEGMENTS
        gap    = min(SEGMENT_GAP, slot_h * 0.4)   # keep a gap only if it fits
        seg_h  = slot_h - gap
        radius = seg_h * 0.45

        span = self.max_val - self.min_val
        frac = (self._value - self.min_val) / span if span else 0.0
        frac = max(0.0, min(1.0, frac))
        filled = int(round(frac * NUM_SEGMENTS))

        painter.setPen(Qt.NoPen)
        for i in range(NUM_SEGMENTS):
            seg_val  = self.min_val + (i / NUM_SEGMENTS) * span
            slot_top = by + bh - (i + 1) * slot_h

            color = self._zone_color(seg_val) if i < filled else EMPTY_COLOR
            painter.setBrush(color)
            painter.drawRoundedRect(
                QRectF(bx, slot_top + gap / 2, bw, seg_h), radius, radius)

    def _draw_ticks(self, painter, fm, tick_col_w, by, bh):
        """Draw scale ticks and labels on the left."""
        painter.setFont(self._tick_font)
        text_w = tick_col_w - TICK_TEXT_PAD - TICK_LEN
        text_h = fm.height()

        num_dec_places = self.num_dec_places if (self.max_val - self.min_val) % NUM_TICKS != 0 else 0

        for i, val in enumerate(self._tick_values()):
            y = by + bh - (i / NUM_TICKS) * bh

            # Tick line
            pen = QPen(TICK_COLOR)
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawLine(int(tick_col_w - TICK_LEN), int(y),
                             int(tick_col_w - 1), int(y))

            # Label
            painter.setPen(LABEL_COLOR)
            painter.drawText(0, int(y - text_h / 2), text_w, text_h,
                             Qt.AlignRight | Qt.AlignVCenter,
                             self._format_tick(val, num_dec_places))

    def _draw_value(self, painter, W, y, value_h, unit_h):
        """Draw the numeric readout and unit below the bar."""
        y = int(y)

        painter.setFont(self._value_font)
        painter.setPen(self._zone_color(self._value))
        painter.drawText(0, y, W, value_h, Qt.AlignCenter, f"{self._value:.{self.num_dec_places}f}")

        if self.unit:
            painter.setFont(self._unit_font)
            painter.setPen(UNIT_COLOR)
            painter.drawText(0, y + value_h, W, unit_h, Qt.AlignCenter, self.unit)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _tick_values(self):
        span = self.max_val - self.min_val
        return [self.min_val + (i / NUM_TICKS) * span
                for i in range(NUM_TICKS + 1)]

    @staticmethod
    def _format_tick(val, num_dec_places):
        return f"{val:.{num_dec_places}f}"

    def _tick_column_width(self, fm):
        widest = max(fm.horizontalAdvance(self._format_tick(v, self.num_dec_places))
                     for v in self._tick_values())
        return widest + TICK_TEXT_PAD + TICK_LEN

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

        # Stretch on both sides keeps the width-capped gauges centered when
        # the window is wider than they need.
        layout.addStretch(1)
        for g in (self.battery, self.fuel, self.temp):
            layout.addWidget(g)
        layout.addStretch(1)

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
    win.resize(640, 400)
    win.show()
    sys.exit(app.exec_())