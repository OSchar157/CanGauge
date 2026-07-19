import sys

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout
)

from can_gauge_app.ui.pages.can_table.can_table import SeenMessagesTable
from can_gauge_app.ui.pages.can_stream.can_stream import RawCanStream
from can_worker.worker import DecodedMsg

class CanPage(QWidget):
    def __init__(self, on_gauge_requested):
        super().__init__()

        master = QHBoxLayout()
        self.setLayout(master)

        left_side = QVBoxLayout()
        master.addLayout(left_side)

        self.raw_can_stream = RawCanStream()
        self.raw_can_stream.setFixedHeight(180)
        self.can_stream_page = SeenMessagesTable(on_gauge_requested=on_gauge_requested)

        left_side.addWidget(self.raw_can_stream)
        left_side.addWidget(self.can_stream_page)

        right_side = QVBoxLayout()
        master.addLayout(right_side)
    
    def on_msgs(self, msgs: list[DecodedMsg]):
        self.can_stream_page.on_msgs(msgs)
        self.raw_can_stream.on_msgs(msgs)