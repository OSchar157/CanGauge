import sys

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QApplication, QVBoxLayout
)

from ui.pages.can_stream.can_messages.can_stream_page import CanStreamPage
from ui.pages.can_stream.raw_can_stream import RawCanStream
from decoding.decoder import DecodedMsg

class CanPage(QWidget):
    def __init__(self):
        super().__init__()

        master = QHBoxLayout()
        self.setLayout(master)

        left_side = QVBoxLayout()
        master.addLayout(left_side)

        self.raw_can_stream = RawCanStream()
        self.raw_can_stream.setFixedHeight(150)
        self.can_stream_page = CanStreamPage()

        left_side.addWidget(self.can_stream_page)
        left_side.addWidget(self.raw_can_stream)

        right_side = QVBoxLayout()
        master.addLayout(right_side)
    
    def on_msg(self, msg: DecodedMsg):
        self.can_stream_page.on_msg(msg)
        self.raw_can_stream.on_msg(msg)