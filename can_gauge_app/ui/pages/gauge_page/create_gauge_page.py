import sys
import json
import math
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QApplication, QPushButton,
    QVBoxLayout, QLabel
)

from PyQt5.QtCore import Qt

from ... import gauge_widgets
from ...gauge_widgets import Gauge

from can import Message
from cantools.database import Database

class CreateGaugePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("No Gauge Pages Initialized"))
        layout.addWidget(QLabel("+"))


