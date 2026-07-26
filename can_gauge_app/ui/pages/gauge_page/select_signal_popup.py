from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QApplication, QPushButton,
    QVBoxLayout, QHBoxLayout, QBoxLayout, QDialog,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QScroller
)
from ui.utils import dec_to_hex, hex_to_dec

from cantools.database import Database
from can.message import Message
from ui.pages.gauge_page.create_gauge_popup import CreateGaugePopup

import worker_manager

class SelectSignalPopup(QDialog):
    def __init__(self, can_db: Database, parent=None):
        super().__init__(parent)
        self.can_db = can_db

        master = QVBoxLayout()
        self.setLayout(master)

        self.setMinimumHeight(600)
        self.setMinimumWidth(500)

        can_msg_tree = QTreeWidget()
        can_msg_tree.setColumnCount(2)
        QScroller.grabGesture(can_msg_tree.viewport(), QScroller.LeftMouseButtonGesture)

        can_msg_tree.setHeaderHidden(True)
        can_msg_tree_header = can_msg_tree.header()
        can_msg_tree_header.setSectionResizeMode(0, QHeaderView.Stretch)
        can_msg_tree_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)

        can_msg_tree.itemClicked.connect(self.signal_clicked)
        master.addWidget(can_msg_tree)

        self.signal_widgets: dict[int, dict[str, QTreeWidgetItem]] = {}

        for msg in self.can_db.messages:
            can_id = msg.frame_id

            can_msg_item = QTreeWidgetItem([f"{dec_to_hex(can_id)} - {msg.name}", ""])
            can_msg_tree.addTopLevelItem(can_msg_item)

            for signal in msg.signals:
                signal_item = QTreeWidgetItem([signal.name, "--"])
                self.signal_widgets.setdefault(can_id, {})[signal.name] = signal_item
                can_msg_item.addChild(signal_item)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        master.addWidget(close_btn)

        self.create_gauge_popup = None

    def signal_clicked(self, item, column):
        if item.parent() is None:
            return
        
        can_id = hex_to_dec(item.parent().text(0).split(" ")[0])
        signal_name = item.text(0)

        self.create_gauge_popup = CreateGaugePopup(self, self.can_db, can_id, signal_name)
        worker_manager.set_owner(self.create_gauge_popup, self.create_gauge_popup.on_msgs)
        
        if self.create_gauge_popup.exec() == QDialog.Accepted:
            self.accept()
        else:
            worker_manager.set_owner(self, self.on_msgs)

    def on_msgs(self, msgs: list[Message]):
        if not msgs:
            return
        
        can_ids_to_update = self.signal_widgets.keys()
        
        for msg in reversed(msgs):
            can_id = msg.arbitration_id
            if can_id not in can_ids_to_update:
                continue
            
            signals = self.can_db.decode_message(can_id, msg.data)
            sig_widgets = self.signal_widgets.get(can_id, {})

            for sig_name, sig_val in signals.items():
                child = sig_widgets.get(sig_name)
                if isinstance(sig_val, float):
                    sig_val = f"{sig_val:.3f}"
                
                child.setText(1, str(sig_val))


import sys
if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()
    db.add_dbc_string(open('subaru_global_TESTING.dbc').read())
    select_signal_popup = SelectSignalPopup(db)
    select_signal_popup.show()
    select_signal_popup.resize(640, 400)
    sys.exit(app.exec_())