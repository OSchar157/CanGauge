import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog,
    QHBoxLayout, QBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator

class DecodeIdPopup(QDialog):
    def __init__(self, parent, id_, ids_seen):
        super().__init__(parent)

        self.data = ids_seen
        self.id_ = id_

        self.setWindowTitle("Decode a Message")
        self.resize(600, 600)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Decode id: {id_}"))

        self._hex_label = QLabel(self.data[self.id_]["data"].raw_hex)
        layout.addWidget(self._hex_label)

        self.setLayout(layout)

    def refresh(self):
        self._hex_label.setText(self.data[self.id_]["data"].raw_hex)