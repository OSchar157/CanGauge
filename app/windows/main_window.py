from PyQt5.QtWidgets import (
    QWidget, QLabel,
    QPushButton, QVBoxLayout, QHBoxLayout,
)
from PyQt5.QtCore import Qt
from app.session import clear_session

class MainWindow(QWidget):
    def __init__(self, username: str = None):
        super().__init__()
        self.username = username
        self.setWindowTitle("Dashboard")
        self.setFixedSize(400, 250)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(30, 30, 30, 30)

        # Welcome message
        welcome = QLabel(f"Welcome, {self.username}!")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(welcome)

        subtitle = QLabel("You are now logged in.")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addStretch()

        # Logout button (bottom-right)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        logout_btn = QPushButton("Log Out")
        logout_btn.setFixedWidth(100)
        logout_btn.clicked.connect(self.handle_logout)
        btn_row.addWidget(logout_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def handle_logout(self):
        from .login import LoginWindow
        clear_session()
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()
