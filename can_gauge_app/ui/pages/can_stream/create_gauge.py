import sys

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QApplication, QLineEdit, QLabel, QVBoxLayout
)

from decoding.decoder import DecodedMsg
from ui.pages.vert_stack import VertStack

class GaugeCreationPage(QWidget):
    def __init__(self, msg: DecodedMsg):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel(msg.name or str(msg.id))
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        signals_layout = QVBoxLayout()
        layout.addWidget(signals_layout)
        for signal in msg.signals.keys():
            box = VertStack(signal, msg.signals[signal])
            signals_layout.addWidget(box)

        