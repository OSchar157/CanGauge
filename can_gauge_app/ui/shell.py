from PyQt5.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QApplication, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt

from ui.pages.gauge_page.gauge_page import GaugePage
from ui.pages.can_table.can_table import CanTable
from ui.pages.can_stream.can_stream import CanStream
from cantools.database import Database
import worker_manager
from .side_menu import SideMenu

BUTTON_LABELS = ["Gauge Display", "Can Table", "Can Stream", "Exit"]

class Shell(QWidget):
    def __init__(self, can_db: Database, parent=None):
        super().__init__(parent)
        self.can_db = can_db

        master = QHBoxLayout(self)
        master.setContentsMargins(0, 0, 0, 0)
        master.setSpacing(0)

        self.page_layout = QVBoxLayout()
        
        self.configure_util_bar()

        self.gauge_page = GaugePage(self, self.can_db)
        self.can_stream_page = CanStream(self.can_db)
        self.can_table_page = CanTable(self.can_db)
        
        self.pages = QStackedWidget()
        self.page_layout.addWidget(self.pages)

        self.pages.addWidget(self.gauge_page)
        self.pages.addWidget(self.can_stream_page)
        self.pages.addWidget(self.can_table_page)

        self.side_menu = SideMenu(BUTTON_LABELS)
        self.side_menu.setVisible(False)
        master.addWidget(self.side_menu)

        master.addLayout(self.page_layout)

        self.side_menu.buttons["Gauge Display"].clicked.connect(lambda: self.show_page(self.gauge_page))
        self.side_menu.buttons["Can Table"].clicked.connect(lambda: self.show_page(self.can_table_page))
        self.side_menu.buttons["Can Stream"].clicked.connect(lambda: self.show_page(self.can_stream_page))
        self.side_menu.buttons["Exit"].clicked.connect(self.on_exit)

        self.show_page(self.can_table_page)
    
    def configure_util_bar(self):
        if hasattr(self, "utility_bar") and self.utility_bar is not None:
            self._clear_layout(self.utility_bar)
        else:
            self.utility_bar = QHBoxLayout()
            # add it to its parent layout ONCE, here, not inside this function again
            self.page_layout.addLayout(self.utility_bar)   # whatever your outer layout is called

        self.hamburger_btn = QPushButton("≡")
        self.hamburger_btn.clicked.connect(self._set_side_menu_vis)
        self.hamburger_btn.setFixedSize(100, 50)
        self.utility_bar.addWidget(self.hamburger_btn)
        
    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def on_exit(self):
        self.gauge_page.save_gauges()
        QApplication.quit()

    def _set_side_menu_vis(self):
        if self.side_menu.isVisible():
            self.side_menu.setVisible(False)
            self.hamburger_btn.setVisible(True)
        else:
            self.side_menu.setVisible(True)
            self.hamburger_btn.setVisible(False)

    def show_page(self, page: QWidget):
        if page == self.pages.currentWidget():
            self.side_menu.setVisible(False)
            self.hamburger_btn.setVisible(True)
            return

        self.configure_util_bar()
        page.configure_util_bar(self.utility_bar)

        if page == self.gauge_page:
            curr_layout = self.gauge_page.layout_pages.currentWidget()
            if getattr(curr_layout, "on_msgs", None):
                worker_manager.set_owner(curr_layout, curr_layout.on_msgs)
            else:
                worker_manager.free()
        else:
            worker_manager.set_owner(page, page.on_msgs)

        self.pages.setCurrentWidget(page)

        self.side_menu.setVisible(False)
        self.hamburger_btn.setVisible(True)