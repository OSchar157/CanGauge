from PyQt5.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication, QPushButton
from PyQt5.QtCore import Qt

from .side_menu import SideMenu


class Shell(QWidget):
    """Persistent layout: side menu on the left, swappable page content on the right."""

    def __init__(self, parent=None):
        super().__init__(parent)

        master = QHBoxLayout(self)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        self.hamburger_btn = QPushButton("≡")
        self.hamburger_btn.clicked.connect(self._set_side_menu_vis)
        master.addWidget(self.hamburger_btn)
        
        self.side_menu = SideMenu()
        self.side_menu.setVisible(False)
        master.addWidget(self.side_menu)

        self.pages = QStackedWidget()
        master.addWidget(self.pages)

        self.side_menu.buttons["Gauge Display"].clicked.connect(lambda: self.show_page("gauge"))
        self.side_menu.buttons["Can Table"].clicked.connect(lambda: self.show_page("cantable"))
        self.side_menu.buttons["Can Stream"].clicked.connect(lambda: self.show_page("canstream"))
        self.side_menu.buttons["Exit"].clicked.connect(QApplication.quit)

        self._page_index = {}
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()
        elif event.key() == Qt.Key_F:
            self.showFullScreen()
        elif event.key() == Qt.Key_S:
            self._set_side_menu_vis()
        elif event.key() == Qt.Key_Q:
            QApplication.quit() 

    def _set_side_menu_vis(self):
        if self.side_menu.isVisible():
            self.side_menu.setVisible(False)
            self.hamburger_btn.setVisible(True)
        else:
            self.side_menu.setVisible(True)
            self.hamburger_btn.setVisible(False)

    def add_page(self, name: str, widget: QWidget):
        index = self.pages.addWidget(widget)
        self._page_index[name] = index

    def show_page(self, name: str):
        self.pages.setCurrentIndex(self._page_index[name])
        self.side_menu.setVisible(False)
        self.hamburger_btn.setVisible(True)