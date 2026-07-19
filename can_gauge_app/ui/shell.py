from PyQt5.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication, QPushButton
from PyQt5.QtCore import Qt

from can_worker.worker import CANWorker
from .side_menu import SideMenu

from ui.keyboard import VirtualKeyboard

BUTTON_LABELS = ["Gauge Display", "Can Table", "Can Stream", "Exit"]

class Shell(QWidget):
    def __init__(self, worker: CANWorker, parent=None):
        super().__init__(parent)

        self.worker = worker

        master = QHBoxLayout(self)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        self.hamburger_btn = QPushButton("≡")
        self.hamburger_btn.clicked.connect(self._set_side_menu_vis)
        master.addWidget(self.hamburger_btn)
        
        self.side_menu = SideMenu(BUTTON_LABELS)
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
        widget.shell = self
        index = self.pages.addWidget(widget)
        self._page_index[name] = index

    def show_page(self, name: str):
        if self._page_index[name] == self.pages.currentIndex():
            self.side_menu.setVisible(False)
            self.hamburger_btn.setVisible(True)

        try:
            cur_page = self.pages.currentWidget()
            self.worker.msg_buffer_emitter.disconnect(cur_page.on_msgs)
        except TypeError:
            pass

        show_page_index = self._page_index[name]
        show_page_widget = self.pages.widget(show_page_index)

        self.worker.msg_buffer_emitter.connect(show_page_widget.on_msgs)
        self.pages.setCurrentIndex(show_page_index)

        self.side_menu.setVisible(False)
        self.hamburger_btn.setVisible(True)