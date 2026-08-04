from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFocusEvent
from PyQt5.QtWidgets import QLineEdit, QWidget, QHBoxLayout, QVBoxLayout, QPushButton
import subprocess

class OnScreenKeyboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.target = None  # the QLineEdit currently being typed into
        self.hide()

        layout = QVBoxLayout(self)
        rows = [
            "1234567890",
            "qwertyuiop",
            "asdfghjkl ",
            "zxcvbnm,.-",
        ]

        for row in rows:
            row_layout = QHBoxLayout()
            for ch in row:
                btn = QPushButton(ch)
                btn.setFixedSize(80, 40)   # tune for your screen
                btn.setStyleSheet("font-size: 24px;")
                btn.setFocusPolicy(Qt.NoFocus)
                btn.clicked.connect(lambda _, c=ch: self._key_pressed(c))
                row_layout.addWidget(btn)
            layout.addLayout(row_layout)

        bottom_row = QHBoxLayout()
        space_btn = QPushButton("Space")
        space_btn.setFocusPolicy(Qt.NoFocus)
        space_btn.clicked.connect(lambda: self._key_pressed(" "))
        space_btn.setStyleSheet("font-size: 20px;")

        back_btn = QPushButton("⌫")
        back_btn.setStyleSheet("font-size: 20px;")
        back_btn.setFocusPolicy(Qt.NoFocus)
        back_btn.clicked.connect(self._backspace)

        hide_btn = QPushButton("↓")
        hide_btn.setStyleSheet("font-size: 20px;")
        hide_btn.setFocusPolicy(Qt.NoFocus)
        hide_btn.clicked.connect(self.hide)

        bottom_row.addWidget(back_btn)
        bottom_row.addWidget(space_btn)
        bottom_row.addWidget(hide_btn)
        layout.addLayout(bottom_row)

    def attach_to(self, line_edit: QLineEdit):
        self.target = line_edit

    def _key_pressed(self, ch):
        if not self.target:
            return

        if not ch == " ":
            self.target.insert(ch)

    def _backspace(self):
        if self.target:
            self.target.backspace()

class KeyboardLineEdit(QLineEdit):
    def __init__(self, keyboard: OnScreenKeyboard, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard = keyboard   # shared instance, passed in

    def focusInEvent(self, event):
        self.keyboard.attach_to(self)
        self.keyboard.show()
        # self.keyboard.raise_()
        super().focusInEvent(event)
