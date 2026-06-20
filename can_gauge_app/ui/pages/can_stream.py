from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import can


class CanStreamPage(QWidget):
    """Simple live CAN stream viewer, styled like `candump`."""

    MAX_LINES = 500  # cap so it doesn't grow forever

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #0a0b0e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Courier New", 11))
        self.text.setStyleSheet(
            "color: #d8dce5; background-color: #0a0b0e; border: none;"
        )
        self.text.setMaximumBlockCount(self.MAX_LINES)  # auto-trims old lines
        layout.addWidget(self.text)

    def add_frame(self, msg: can.Message):
        """Call this for every incoming frame. Matches candump's layout."""
        hex_bytes = " ".join(f"{b:02X}" for b in msg.data)
        line = f"{msg.channel}  {msg.arbitration_id:03X}   [{msg.dlc}]  {hex_bytes}"
        self.text.appendPlainText(line)

        scrollbar = self.text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())