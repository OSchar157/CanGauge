from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QDialog
from PyQt5.QtCore import Qt

class ConfirmPopup(QDialog):
    def __init__(self, message: str, parent=None):
        super().__init__(parent)

        self.setFixedSize(450, 220)

        master = QVBoxLayout()
        master.setContentsMargins(20, 20, 20, 20)
        master.setSpacing(16)
        self.setLayout(master)

        label = QLabel(message)
        label.setStyleSheet("font-size: 18px;")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        master.addWidget(label)

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(12)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setFixedHeight(60)
        confirm_btn.setStyleSheet("font-size: 18px;")
        confirm_btn.clicked.connect(self.accept)
        btns_layout.addWidget(confirm_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(60)
        cancel_btn.setStyleSheet("font-size: 18px;")
        cancel_btn.clicked.connect(self.reject)
        btns_layout.addWidget(cancel_btn)

        master.addLayout(btns_layout)