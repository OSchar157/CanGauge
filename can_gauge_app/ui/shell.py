from PyQt5.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt

import worker_manager
from .side_menu import SideMenu

BUTTON_LABELS = ["Gauge Display", "Can Table", "Can Stream", "Exit"]

class Shell(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        master = QHBoxLayout(self)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        btn_page_layout = QVBoxLayout()

        self.hamburger_btn = QPushButton("≡")
        self.hamburger_btn.clicked.connect(self._set_side_menu_vis)
        self.hamburger_btn.setFixedSize(100, 50)
        btn_page_layout.addWidget(self.hamburger_btn)
        
        self.pages = QStackedWidget()
        btn_page_layout.addWidget(self.pages)

        self.side_menu = SideMenu(BUTTON_LABELS)
        self.side_menu.setVisible(False)
        master.addWidget(self.side_menu)

        master.addLayout(btn_page_layout)

        self.side_menu.buttons["Gauge Display"].clicked.connect(lambda: self.show_page("gauge"))
        self.side_menu.buttons["Can Table"].clicked.connect(lambda: self.show_page("cantable"))
        self.side_menu.buttons["Can Stream"].clicked.connect(lambda: self.show_page("canstream"))
        self.side_menu.buttons["Exit"].clicked.connect(self.on_exit)

        self._page_index = {}
    
    def on_exit(self):
        idx = self._page_index["gauge"]
        self.pages.widget(idx).save_gauges()
        QApplication.quit()
    
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
        if self._page_index[name] == self.pages.currentIndex():
            self.side_menu.setVisible(False)
            self.hamburger_btn.setVisible(True)

        show_page_index = self._page_index[name]
        show_page_widget = self.pages.widget(show_page_index)

        worker_manager.set_owner(show_page_widget, show_page_widget.on_msgs)
        self.pages.setCurrentIndex(show_page_index)

        self.side_menu.setVisible(False)
        self.hamburger_btn.setVisible(True)