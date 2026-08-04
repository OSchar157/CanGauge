import sys
import json
import math
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QApplication, QPushButton,
    QVBoxLayout, QStackedWidget, QDialog, QHBoxLayout
)

import worker_manager


from PyQt5.QtCore import Qt

from ... import gauge_widgets
from ...gauge_widgets import Gauge

from can import Message
from cantools.database import Database

from ui.pages.gauge_page.new_gauge_layout_page import CreateGaugeLayoutPage, CreateGaugeLayoutPagePopup
from ui.pages.gauge_page.layout_presets.dual_row_layout_preset import DualRowGaugeLayout
from ui.confirm_popup import ConfirmPopup
from ui.pages.gauge_page.layout_presets import GAUGE_LAYOUT_PAGE_TYPES

SAVE_FILE = Path(__file__).with_name("gauge_save.json")

class GaugePage(QWidget):
    def __init__(self, shell, can_db: Database):
        super().__init__()

        self.shell = shell
        self.can_db = can_db

        master = QVBoxLayout()
        self.setLayout(master)

        self.utility_bar = QHBoxLayout()
        master.addLayout(self.utility_bar)

        self.layout_pages = QStackedWidget()
        master.addWidget(self.layout_pages)
        self.new_gauge_layout_page = CreateGaugeLayoutPage()
        self.new_gauge_layout_page.clicked.connect(self.add_gauge_layout_page)

        self.layout_pages.addWidget(self.new_gauge_layout_page)
        self.layout_pages.setCurrentWidget(self.new_gauge_layout_page)

        self.load_pages_and_gauges()

    def configure_util_bar(self, util_bar_layout):
        nav_btns_layout = QHBoxLayout()

        page_left = QPushButton("<")
        page_left.clicked.connect(lambda: self.pan_page(True))
        nav_btns_layout.addWidget(page_left)
        
        page_right = QPushButton(">")
        page_right.clicked.connect(lambda: self.pan_page(False))
        nav_btns_layout.addWidget(page_right)

        util_bar_layout.addLayout(nav_btns_layout)

        rm_page_btn = QPushButton("Remove Page")
        rm_page_btn.clicked.connect(self.remove_cur_page)
        util_bar_layout.addWidget(rm_page_btn)

    def remove_cur_page(self):
        cur_idx = self.layout_pages.currentIndex()

        if cur_idx == 0:
            return

        confirm_popup = ConfirmPopup("Are you sure you want to delete this page?", self)

        if confirm_popup.exec() != QDialog.Accepted:
            return
        
        widget_to_rm = self.layout_pages.widget(cur_idx)
        self.layout_pages.removeWidget(widget_to_rm)

        if self.layout_pages.count() == 1:
            worker_manager.free()
        else:
            cur_idx = self.layout_pages.currentIndex()
            cur_widget = self.layout_pages.widget(cur_idx)
            worker_manager.set_owner(cur_widget, cur_widget.on_msgs)

        widget_to_rm.deleteLater()

    def pan_page(self, left: bool = True):
        num_pages = self.layout_pages.count()
        if num_pages == 1:
            return

        max_page_idx = num_pages - 1
        endpoint = 0 if left else max_page_idx

        cur_idx = self.layout_pages.currentIndex()
        if (cur_idx == endpoint) and left:
            self.layout_pages.setCurrentIndex(max_page_idx)
        elif (cur_idx == endpoint) and (not left):
            self.layout_pages.setCurrentIndex(0)
        else:
            dir = -1 if left else 1
            self.layout_pages.setCurrentIndex(cur_idx + dir)

        cur_widget = self.layout_pages.currentWidget()
        if cur_widget == self.new_gauge_layout_page:
            worker_manager.free()
        else:
            worker_manager.set_owner(cur_widget, cur_widget.on_msgs)
        
    def add_gauge_layout_page(self):
        select_layout_type = CreateGaugeLayoutPagePopup()

        if select_layout_type.exec() != QDialog.Accepted:
            return

        for type in GAUGE_LAYOUT_PAGE_TYPES:
            if type.name == select_layout_type.selected_layout_type_name:
                selected_layout = type

        new_layout_page = selected_layout(self.can_db)
        self.layout_pages.addWidget(new_layout_page)
        self.layout_pages.setCurrentWidget(new_layout_page)
        worker_manager.set_owner(new_layout_page, new_layout_page.on_msgs)

    def save_gauges(self):
        pages = []
        for i in range(self.layout_pages.count()):
            widget = self.layout_pages.widget(i)
            if not hasattr(widget, "json"):
                continue  # e.g. the "create new layout" placeholder page
            pages.append({
                "layout_type": type(widget).__name__,
                "gauges": widget.json(),
            })

        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(pages, f, indent=2)
        except (OSError, TypeError) as e:
            print(f"Failed to save gauges: {e}")

    def load_pages_and_gauges(self):
        if not SAVE_FILE.exists():
            return

        try:
            with open(SAVE_FILE) as f:
                pages = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Failed to load gauges: {e}")
            return

        for page_data in pages:
            layout_cls = next(
                (t for t in GAUGE_LAYOUT_PAGE_TYPES if t.__name__ == page_data["layout_type"]),
                None,
            )
            if layout_cls is None:
                print(f"Unknown layout type in save file: {page_data['layout_type']}")
                continue

            new_layout_page = layout_cls(self.can_db)
            new_layout_page.load_gauges(page_data["gauges"])
            self.layout_pages.addWidget(new_layout_page)

        if self.layout_pages.count() > 1:
            self.layout_pages.setCurrentIndex(1)
            cur_widget = self.layout_pages.currentWidget()
            worker_manager.set_owner(cur_widget, cur_widget.on_msgs)
        