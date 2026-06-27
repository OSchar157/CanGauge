from PyQt5.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication
from PyQt5.QtCore import Qt, QElapsedTimer

from .side_menu import SideMenu


class Shell(QWidget):
    """Persistent layout: side menu on the left, swappable page content on the right."""

    def __init__(self, parent=None):
        super().__init__(parent)

        master = QHBoxLayout(self)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        self.side_menu = SideMenu()
        self.side_menu.setVisible(False)
        master.addWidget(self.side_menu)

        self.pages = QStackedWidget()
        master.addWidget(self.pages)

        self.side_menu.buttons["Gauge Display"].clicked.connect(lambda: self.show_page("gauge"))
        self.side_menu.buttons["Can Stream"].clicked.connect(lambda: self.show_page("canpage"))
        self.side_menu.buttons["Exit"].clicked.connect(QApplication.quit)

        self._page_index = {}

        # self.tap_timer = QElapsedTimer()
        # self.tap_timer.start()
        # self.last_tap_valid = False
        # self.double_tap_threshold = 400  # ms
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()
        elif event.key() == Qt.Key_F:
            self.showFullScreen()
        elif event.key() == Qt.Key_S:
            self._set_side_menu_vis()
        elif event.key() == Qt.Key_Q:
            QApplication.quit() 

    # def mousePressEvent(self, event):
    #     elapsed = self.tap_timer.elapsed()
    #     if self.last_tap_valid and elapsed < self.double_tap_threshold:
    #         self._set_side_menu_vis()
    #         self.last_tap_valid = False  # reset so triple-tap doesn't trigger again
    #     else:
    #         self.last_tap_valid = True
    #         self.tap_timer.restart()
    
    def _set_side_menu_vis(self):
        if self.side_menu.isVisible():
            self.side_menu.setVisible(False)
        else:
            self.side_menu.setVisible(True)

    def add_page(self, name: str, widget: QWidget):
        index = self.pages.addWidget(widget)
        self._page_index[name] = index

    def show_page(self, name: str):
        self.pages.setCurrentIndex(self._page_index[name])
        self.side_menu.setVisible(False)