import time

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QPushButton,
    QCheckBox
)

from decoding.decoder import DecodedMsg
import math

from ..styling import (
    ROW_BG, ROW_BG_HOVER, ACCENT, 
    MONO, TEXT_FG, HEADER_FG, ID_FG,
    ROW_BORDER
    )

class ExpandableMessageRow(QWidget):
    """
    Wraps a FrameRow. Clicking it expands a panel below listing every
    decoded signal in that message as a checkbox, so the user can select
    one or more signals (all from this same CAN ID) to build a gauge from.
    """

    def __init__(self, frame: DecodedMsg, parent=None):
        super().__init__(parent)
        self.can_id = frame.can_id
        self.expanded = False
        self._chips: dict[str, SubMessage] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # the clickable summary row
        self.row = MessageRow(frame)
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
                chip = SubMessage(name, value)
                self._chips[name] = chip
                panel_layout.addWidget(chip)
        else:
            empty_label = QLabel("No decoded signals for this ID (not in loaded DBC)")
            empty_label.setFont(QFont(MONO, 9))
            empty_label.setStyleSheet(f"color: {HEADER_FG}; padding: 8px 24px;")
            panel_layout.addWidget(empty_label)

        create_gauge_btn = QPushButton("Create Gauge")
        create_gauge_btn.setCursor(Qt.PointingHandCursor)
        create_gauge_btn.setFont(QFont(MONO, 10, QFont.Bold))
        create_gauge_btn.setFixedSize(110, 25)
        create_gauge_btn.setStyleSheet(
            f"""
                QPushButton {{
                    background-color: #FF0000;
                    color: {TEXT_FG};
                    border: 1px solid #FF0000;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {ROW_BG_HOVER};
                }}
            """
        )
        create_gauge_btn.clicked.connect(self.create_gauge)
        panel_layout.addWidget(create_gauge_btn)

        self.panel.setVisible(False)
        outer.addWidget(self.panel)

    def create_gauge(self):
        selected_signals = []
        for name, chip in self._chips.items():
            if chip.check_box.isChecked():
                selected_signals.append(name)
        print(selected_signals)
        print("next job nigga")

    def _toggle_expanded(self, _frame):
        self.expanded = not self.expanded
        self.panel.setVisible(self.expanded)

    def _update_data(self, new_msg: DecodedMsg):
        self.setUpdatesEnabled(False)
        self.row._update_data(new_msg)

        for name, value in new_msg.signals.items():
            if name in self._chips:
                self._chips[name].update_value(value)

        self.setUpdatesEnabled(True)
        self.update()

class MessageRow(QWidget):
    """A single clickable CAN-message'box' — one row in the stream."""

    clicked = pyqtSignal(DecodedMsg)

    def __init__(self, msg: DecodedMsg, parent=None):
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

        self.ts_label = self._cell(format_time(msg.timestamp), mono, TEXT_FG, 130)
        self.channel_label = self._cell(msg.channel, mono, TEXT_FG, 80)
        self.id_label = self._cell(f"{msg.can_id:03X}", QFont(MONO, 11, QFont.Bold), ID_FG, 70)
        self.dlc_label = self._cell(f"[{msg.dlc}]", mono, HEADER_FG, 50)
        self.name_label = self._cell(f"{"" if msg.name is None else msg.name}", mono, HEADER_FG, 150)

        self.data_label = self._cell(msg.raw_hex, mono, TEXT_FG, None)
        self.data_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        for w in (self.ts_label, self.channel_label, self.id_label, self.dlc_label, self.name_label, self.data_label):
            layout.addWidget(w)

    def mousePressEvent(self, event):
        self.clicked.emit(self.msg)
        super().mousePressEvent(event)

    def _cell(self, text, font, color, fixed_width):
        lbl = QLabel(text)
        lbl.setFont(font)
        lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        if fixed_width:
            lbl.setFixedWidth(fixed_width)
        return lbl

    def _update_data(self, new_msg: DecodedMsg):
        self.setUpdatesEnabled(False)

        self.ts_label.setText(format_time(new_msg.timestamp))
        self.channel_label.setText(new_msg.channel)
        self.id_label.setText(str(new_msg.can_id))
        self.dlc_label.setText(f"[{new_msg.dlc}]")
        self.name_label.setText(new_msg.name)
        self.data_label.setText(new_msg.raw_hex)

        self.setUpdatesEnabled(True)
        self.update()


class SubMessage(QWidget):
    """One selectable signal inside an expanded frame — checkbox + name + live value."""

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
        self.value_label.setFixedWidth(60)
        layout.addWidget(self.value_label)

        self.check_box = QCheckBox()
        self.check_box.setChecked(False)
        layout.addWidget(self.check_box)

        layout.addStretch()

    def update_value(self, value):
        if type(value) is float:
            value = round(value, 4)
        self.value_label.setText(str(value))


def format_time(timestamp):
    return time.strftime("%H:%M:%S", time.localtime(timestamp or time.time())) + f".{int((timestamp or 0) % 1 * 1000):03d}"