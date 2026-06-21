import time

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
)

from decoding.decoder import DecodedFrame

# ── palette (matches the dark cockpit look used elsewhere) ──
BG = "#0a0b0e"
ROW_BG = "#16181d"
ROW_BG_LIGHT = "#1c1f25"
ROW_BG_HOVER = "#4A5361"
ROW_BORDER = "#262932"
HEADER_FG = "#6f7480"
TEXT_FG = "#d8dce5"
ID_FG = "#7fd9c4"
ACCENT = "#dc3c28"
MONO = "Courier New"


class FrameRow(QWidget):
    """A single clickable CAN-frame 'box' — one row in the stream."""

    clicked = pyqtSignal(DecodedFrame)

    def __init__(self, msg: DecodedFrame, parent=None):
        super().__init__(parent)
        self.msg = msg
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("frameRow")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#frameRow {{
                background-color: {ROW_BG};
                border: 1px solid {ROW_BG};
                border-radius: 2px;
            }}
            QWidget#frameRow:hover {{
                background-color: {ROW_BG_HOVER};
                border: 1px solid {ACCENT};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(0)

        mono = QFont(MONO, 11)

        self.ts_label = self._cell(
            time.strftime("%H:%M:%S", time.localtime(msg.timestamp or time.time()))
            + f".{int((msg.timestamp or 0) % 1 * 1000):03d}",
            mono, TEXT_FG, 130
        )
        self.iface_label = self._cell(msg.channel, mono, TEXT_FG, 80)
        self.id_label = self._cell(f"{msg.can_id:03X}", QFont(MONO, 11, QFont.Bold), ID_FG, 70)
        self.dlc_label = self._cell(f"[{msg.dlc}]", mono, HEADER_FG, 50)
        self.name_label = self._cell(f"{"" if msg.name is None else msg.name}", mono, HEADER_FG, 150)

        self.data_label = self._cell(msg.raw_hex, mono, TEXT_FG, None)
        self.data_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        for w in (self.ts_label, self.iface_label, self.id_label, self.dlc_label, self.name_label, self.data_label):
            layout.addWidget(w)

    def _cell(self, text, font, color, fixed_width):
        lbl = QLabel(text)
        lbl.setFont(font)
        lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        if fixed_width:
            lbl.setFixedWidth(fixed_width)
        return lbl

    def mousePressEvent(self, event):
        self.clicked.emit(self.msg)
        super().mousePressEvent(event)

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

class SignalChip(QWidget):
    """One selectable signal inside an expanded frame — checkbox + name + live value."""

    toggled = pyqtSignal(str, bool)  # signal_name, checked

    def __init__(self, name: str, value, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 4, 12, 4)
        layout.setSpacing(10)

        name_label = QLabel(name)
        name_label.setFont(QFont(MONO, 10, QFont.Bold))
        name_label.setStyleSheet(f"color: {TEXT_FG};")
        name_label.setFixedWidth(160)
        layout.addWidget(name_label)

        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont(MONO, 10))
        self.value_label.setStyleSheet(f"color: {HEADER_FG};")
        layout.addWidget(self.value_label)

        layout.addStretch()

    def update_value(self, value):
        self.value_label.setText(str(value))


class ExpandableFrameRow(QWidget):
    """
    Wraps a FrameRow. Clicking it expands a panel below listing every
    decoded signal in that message as a checkbox, so the user can select
    one or more signals (all from this same CAN ID) to build a gauge from.
    """

    signals_selected = pyqtSignal(int, list)  # can_id, [signal_names]

    def __init__(self, frame: DecodedFrame, parent=None):
        super().__init__(parent)
        self.can_id = frame.can_id
        self.expanded = False
        self.selected_signals: set[str] = set()
        self._chips: dict[str, SignalChip] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # the existing clickable summary row
        self.row = FrameRow(frame)
        self.row.clicked.connect(self._toggle_expanded)
        outer.addWidget(self.row)

        # expandable panel — hidden until clicked
        self.panel = QWidget()
        self.panel.setObjectName("signalPanel")
        self.panel.setAttribute(Qt.WA_StyledBackground, True)
        self.panel.setStyleSheet(f"""
            QWidget#signalPanel {{
                background-color: {ROW_BG};
                border: 1px solid {ROW_BORDER};
                border-top: none;
                border-radius: 2px;
            }}
        """)
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(0, 6, 0, 8)
        panel_layout.setSpacing(2)

        if frame.signals:
            for name, value in frame.signals.items():
                chip = SignalChip(name, value)
                self._chips[name] = chip
                panel_layout.addWidget(chip)
        else:
            empty_label = QLabel("No decoded signals for this ID (not in loaded DBC)")
            empty_label.setFont(QFont(MONO, 9))
            empty_label.setStyleSheet(f"color: {HEADER_FG}; padding: 8px 24px;")
            panel_layout.addWidget(empty_label)

        self.panel.setVisible(False)
        outer.addWidget(self.panel)

    def _toggle_expanded(self, _frame):
        self.expanded = not self.expanded
        self.panel.setVisible(self.expanded)

    def update_frame(self, frame: DecodedFrame):
        """Call on every new frame with this can_id to keep live values fresh."""
        for name, value in frame.signals.items():
            if name in self._chips:
                self._chips[name].update_value(value)

class ColumnHeader(QWidget):
    """Header labels above the stream, matching FrameRow's column widths."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 8)
        layout.setSpacing(0)

        font = QFont(MONO, 12, QFont.Bold)

        for text, width in [
            ("TIMESTAMP", 110),
            ("INTERFACE", 100),
            ("ID", 70),
            ("LEN", 100),
            ("NAME", 150)
        ]:
            lbl = QLabel(text)
            lbl.setFont(font)
            lbl.setStyleSheet(f"color: {HEADER_FG}; letter-spacing: 1px;")
            lbl.setFixedWidth(width)
            layout.addWidget(lbl)

        data_lbl = QLabel("DATA")
        data_lbl.setFont(font)
        data_lbl.setStyleSheet(f"color: {HEADER_FG}; letter-spacing: 1px;")
        layout.addWidget(data_lbl)


class CanStreamPage(QWidget):
    """Live CAN stream viewer — header row + scrolling list of clickable frame boxes."""

    MAX_ROWS = 500  # cap so it doesn't grow forever

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self.paused = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        self.frame_count = 0

        # ── top bar: title + pause button ──
        top_bar = QHBoxLayout()
        title = QLabel("CAN STREAM")
        title.setFont(QFont(MONO, 13, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_FG};")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self.pause_btn = QPushButton("⏸  Pause")
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.setFont(QFont(MONO, 10, QFont.Bold))
        self.pause_btn.setFixedSize(110, 34)
        self.pause_btn.setStyleSheet(self._pause_btn_style(paused=False))
        self.pause_btn.clicked.connect(self.toggle_pause)
        top_bar.addWidget(self.pause_btn)

        outer.addLayout(top_bar)

        # ── column headers ──
        outer.addWidget(ColumnHeader())

        # ── scrollable row list ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {BG}; }}
            QScrollBar:vertical {{ background: {BG}; width: 10px; }}
            QScrollBar::handle:vertical {{ background: {ROW_BORDER}; border-radius: 5px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.row_container = QWidget()
        self.row_container.setStyleSheet(f"background-color: {BG};")
        self.row_layout = QVBoxLayout(self.row_container)
        self.row_layout.setContentsMargins(0, 0, 0, 0)
        self.row_layout.setSpacing(6)
        self.row_layout.addStretch()  # keeps rows pinned to top as they're inserted

        self.scroll_area.setWidget(self.row_container)
        outer.addWidget(self.scroll_area)

        self._rows = []  # track FrameRow widgets for trimming

    def _pause_btn_style(self, paused: bool):
        bg = ACCENT if paused else ROW_BG
        border = ACCENT
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {TEXT_FG};
                border: 1px solid {border};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {ROW_BG_HOVER if not paused else ACCENT};
            }}
        """
    
    def on_frame(self, frame: DecodedFrame):
        self.add_frame(frame)

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.setText("▶  Resume" if self.paused else "⏸  Pause")
        self.pause_btn.setStyleSheet(self._pause_btn_style(self.paused))

    def add_frame(self, msg: DecodedFrame):
        """Call this for every incoming frame. Skips updates while paused."""
        if self.paused:
            return

        self.frame_count += 1

        if len(msg.signals) > 1:
            row = ExpandableFrameRow(msg)
        else:
            row = FrameRow(msg)

        # insert at top (index 0, before the trailing stretch)
        self.row_layout.insertWidget(0, row)
        self._rows.insert(0, row)

        # trim old rows past the cap
        while len(self._rows) > self.MAX_ROWS:
            old_row = self._rows.pop()
            self.row_layout.removeWidget(old_row)
            old_row.deleteLater()

    def _on_create_gauge_clicked(self, can_id: int, signal_names: list):
        print(f"Create gauge: id={can_id:03X}, signals={signal_names}")
        # gauge creation flow goes here later