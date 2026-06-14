import sys
from PyQt5.QtWidgets import QApplication

from windows.login import LoginWindow
from windows.main_window import MainWindow
from session import load_session

if __name__ == "__main__":
    app = QApplication(sys.argv)

    session = load_session()
    print(session)
    if session:
        window = MainWindow(session["username"])
    else:
        window = LoginWindow()
    window.show()
    sys.exit(app.exec_())