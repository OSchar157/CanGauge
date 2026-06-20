import time

import can
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

    clicked = pyqtSignal(can.Message)

    def __init__(self, msg: can.Message, isLight: bool, parent=None):
        super().__init__(parent)
        self.msg = msg
        self.isLight = isLight
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("frameRow")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#frameRow {{
                background-color: {ROW_BG_LIGHT if isLight else ROW_BG};
                border: 1px solid {ROW_BG_LIGHT if isLight else ROW_BG};
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
        self.id_label = self._cell(f"{msg.arbitration_id:03X}", QFont(MONO, 11, QFont.Bold), ID_FG, 70)
        self.dlc_label = self._cell(f"[{msg.dlc}]", mono, HEADER_FG, 50)

        hex_bytes = " ".join(f"{b:02X}" for b in msg.data)
        self.data_label = self._cell(hex_bytes, mono, TEXT_FG, None)
        self.data_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        for w in (self.ts_label, self.iface_label, self.id_label, self.dlc_label, self.data_label):
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
            ("LEN", 50),
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
    frame_clicked = pyqtSignal(can.Message)

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

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.setText("▶  Resume" if self.paused else "⏸  Pause")
        self.pause_btn.setStyleSheet(self._pause_btn_style(self.paused))

    def add_frame(self, msg: can.Message):
        """Call this for every incoming frame. Skips updates while paused."""
        if self.paused:
            return

        lightFrame = True if self.frame_count % 2 == 0 else False
        self.frame_count += 1

        row = FrameRow(msg, isLight=True)
        row.clicked.connect(self.frame_clicked.emit)

        # insert at top (index 0, before the trailing stretch)
        self.row_layout.insertWidget(0, row)
        self._rows.insert(0, row)

        # trim old rows past the cap
        while len(self._rows) > self.MAX_ROWS:
            old_row = self._rows.pop()
            self.row_layout.removeWidget(old_row)
            old_row.deleteLater()