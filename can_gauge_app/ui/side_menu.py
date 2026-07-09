from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

class SideMenu(QWidget):
    def __init__(self, parent=None, width=220):
        super().__init__(parent)
        self.setFixedWidth(width)
        self.setStyleSheet("background-color: #1a1b1f;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        title = QLabel("Settings")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.buttons = {}
        for label in ["Gauge Display", "Can Stream", "Can Table", "Exit"]:
            btn = QPushButton(label)
            btn.setStyleSheet("color: white; text-align: left; padding: 10px; border: none;")
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
            self.buttons[label] = btn


        layout.addStretch()