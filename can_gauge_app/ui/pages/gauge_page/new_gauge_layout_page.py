import sys
import json
import math
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QApplication, QPushButton,
    QVBoxLayout, QLabel, QDialog, QComboBox
)

from PyQt5.QtCore import Qt, pyqtSignal

from ... import gauge_widgets
from ...gauge_widgets import Gauge

from ui.pages.gauge_page.layout_presets import GAUGE_LAYOUT_PAGE_TYPES

from can import Message
from cantools.database import Database

class CreateGaugeLayoutPage(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Add a New Page")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 22px;")

        plus_label = QLabel("+")
        plus_label.setAlignment(Qt.AlignCenter)
        plus_label.setStyleSheet("font-size: 48px;")

        layout.addWidget(title_label)
        layout.addWidget(plus_label)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

class CreateGaugeLayoutPagePopup(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setFixedSize(500, 350)   # roomy fixed popup for a 1024x600 screen

        master = QVBoxLayout()
        master.setContentsMargins(20, 20, 20, 20)
        master.setSpacing(16)
        self.setLayout(master)

        title_label = QLabel("Select a Gauge Layout:")
        title_label.setStyleSheet("font-size: 20px;")
        master.addWidget(title_label)

        self.layout_opts = QComboBox()
        self.layout_opts.addItems([type.name for type in GAUGE_LAYOUT_PAGE_TYPES])
        self.layout_opts.setFixedHeight(60)
        self.layout_opts.setStyleSheet("""
            QComboBox {
                font-size: 18px;
            }
            QComboBox QAbstractItemView {
                font-size: 18px;
                min-height: 60px;
            }
            QComboBox QAbstractItemView::item {
                min-height: 60px;
                padding: 8px;
            }
        """)
        self.selected_layout_type_name = self.layout_opts.currentText()
        master.addWidget(self.layout_opts)

        btns_layout = QVBoxLayout()
        btns_layout.setSpacing(12)

        save_btn = QPushButton("Confirm")
        save_btn.setFixedHeight(50)
        save_btn.setStyleSheet("font-size: 18px;")
        save_btn.clicked.connect(self.on_confirm)
        btns_layout.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(50)
        close_btn.setStyleSheet("font-size: 18px;")
        close_btn.clicked.connect(self.reject)
        btns_layout.addWidget(close_btn)

        master.addLayout(btns_layout)

    def on_confirm(self):
        self.selected_layout_type_name = self.layout_opts.currentText()
        self.accept()