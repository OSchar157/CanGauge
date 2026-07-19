from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QMessageBox
)

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(320, 200)
        self._build_ui()

    def _build_ui(self):
        # Encapsulates username, password, login btn
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 30, 30)

        # Username row
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        layout.addWidget(self.username_input)

        # Password row
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        # Login button
        login_btn = QPushButton("Log In")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)

        # New User button
        newusr_btn = QPushButton("New User")
        newusr_btn.setFixedWidth(100)
        newusr_btn.clicked.connect(self.handle_newusr)
        layout.addWidget(newusr_btn)

        # Allow pressing Enter to submit
        self.password_input.returnPressed.connect(self.handle_login)

        self.setLayout(layout)

    def handle_login(self):
        from .main_window import MainWindow

        username = self.username_input.text().strip()
        password = self.password_input.text()

        # Simple hardcoded check — swap in real auth here
        if username == "admin" and password == "admin":
            self.main_window = MainWindow(username)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            self.password_input.clear()
            self.password_input.setFocus()

    def handle_newusr(self):
        print("new user nigga")

