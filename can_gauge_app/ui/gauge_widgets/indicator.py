import sys
from enum import Enum

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QSize
from PyQt5.QtGui import QPainter, QColor, QFont

from can_gauge_app.ui.gauge_widgets.gauge import ParamSpec 

# TODO: possible future customization: additional modes (>, <, !=), an "invert" flag,
#       hysteresis around thresholds, blink/flash on activation, alternate icon shapes,
#       a Qt signal emitted on state change


INDICATOR_OFF_COLOR = "#5a5a5a"
INDICATOR_ON_COLOR = "#E8A020"   # same orange as NeedleGauge's warning zone / needle

FACE_BEZEL_COLOR = "#1a1a1a"
FACE_COLOR = "#111111"
LABEL_COLOR = "#cccccc"


class IndicatorMode(str, Enum):
    EQUALS = "equals"
    BETWEEN = "between"
    OUTSIDE = "outside"


class Indicator(QWidget):
    """
    Simple on/off indicator lamp. Does NOT inherit Gauge — it's a plain QWidget
    that lights up orange when its condition is met, grey otherwise.

    Trigger modes (checked against the live value passed to set_value()):
        "equals"  -> abs(value - target) <= tolerance
        "between" -> low <= value <= high
        "outside" -> value < low or value > high

    To add a new mode: add a value to IndicatorMode, write a "_check_<mode>"
    method, and register it in self._evaluators.
    """

    name = "Indicator"

    @classmethod
    def get_fields(cls) -> list[ParamSpec]:
        return [
            ParamSpec("label", "Label", str, "INDICATOR"),
            ParamSpec("mode", "Mode", str, IndicatorMode.EQUALS.value),
            ParamSpec("target", "Target Value", float, 0.0),
            ParamSpec("low", "Low Endpoint", float, 0.0),
            ParamSpec("high", "High Endpoint", float, 100.0),
            ParamSpec("tolerance", "Tolerance", float, 0.0),
        ]

    def __init__(
        self,
        label: str,
        mode: str = IndicatorMode.EQUALS.value,
        target: float = 0.0,
        low: float = 0.0,
        high: float = 100.0,
        tolerance: float = 0.0,
        parent=None,
    ):
        super().__init__(parent)

        try:
            mode = IndicatorMode(mode)
        except ValueError:
            valid = ", ".join(m.value for m in IndicatorMode)
            raise ValueError(f"mode must be one of: {valid} (got {mode!r}).")

        if mode in (IndicatorMode.BETWEEN, IndicatorMode.OUTSIDE) and low >= high:
            raise ValueError("low must be less than high for 'between'/'outside' modes.")

        if tolerance < 0:
            raise ValueError("tolerance must be >= 0.")

        self.label = label
        self.mode = mode
        self.target = target
        self.low = low
        self.high = high
        self.tolerance = tolerance

        self._value = None
        self._on = False

        # dispatch table — add an entry here when adding a new mode
        self._evaluators = {
            IndicatorMode.EQUALS: self._check_equals,
            IndicatorMode.BETWEEN: self._check_between,
            IndicatorMode.OUTSIDE: self._check_outside,
        }

    def sizeHint(self):
        return QSize(120, 120)

    # ── Value / state ────────────────────────────────────────────────────────

    def set_value(self, value):
        self._value = value
        new_state = False if value is None else self._evaluators[self.mode]()
        if new_state != self._on:
            self._on = new_state
            self.update()

    @property
    def is_on(self) -> bool:
        return self._on

    def _check_equals(self) -> bool:
        return abs(self._value - self.target) <= self.tolerance

    def _check_between(self) -> bool:
        return self.low <= self._value <= self.high

    def _check_outside(self) -> bool:
        return self._value < self.low or self._value > self.high

    # ── Painting ─────────────────────────────────────────────────────────────

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
        painter.setWindow(-50, -50, 100, 100)

        self._draw_background(painter)
        self._draw_icon(painter)
        self._draw_label(painter)

    def _draw_background(self, painter: QPainter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(FACE_BEZEL_COLOR))
        painter.drawEllipse(-50, -50, 100, 100)
        painter.setBrush(QColor(FACE_COLOR))
        painter.drawEllipse(-44, -44, 88, 88)

    def _draw_icon(self, painter: QPainter):
        color = QColor(INDICATOR_ON_COLOR if self._on else INDICATOR_OFF_COLOR)
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)

        # stem
        painter.drawRoundedRect(QRectF(-6, -36, 12, 26), 6, 6)
        # dot
        painter.drawEllipse(QPointF(0, 0), 6, 6)

    def _draw_label(self, painter: QPainter):
        painter.setPen(QColor(LABEL_COLOR))
        font = QFont("Courier New", 8, QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(-42, 9, 84, 30),
            Qt.AlignCenter | Qt.TextWordWrap,
            self.label,
        )


# ── Demo window ─────────────────────────────────────────────────────────────

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Indicator Demo")
        self.setStyleSheet("background-color: #0d0d0d;")

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.ind_equals = Indicator("COOLANT", mode="equals", target=50, tolerance=2)
        self.ind_between = Indicator("IN RANGE", mode="between", low=30, high=70)
        self.ind_outside = Indicator("OUT OF RANGE", mode="outside", low=30, high=70)

        for ind in (self.ind_equals, self.ind_between, self.ind_outside):
            layout.addWidget(ind)

        self.setLayout(layout)

        # Animate value for demo, same pattern as the needle gauge demo
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
        for ind in (self.ind_equals, self.ind_between, self.ind_outside):
            ind.set_value(self._demo_value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DemoWindow()
    win.resize(420, 160)
    win.show()
    sys.exit(app.exec_())