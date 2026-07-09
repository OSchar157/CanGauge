from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from can_worker.worker import DecodedMsg
from ui.pages.can_table.create_gauge_popup import CreateGaugePopup
from collections import defaultdict

class CanTable(QWidget):
    data_updated = pyqtSignal()

    def __init__(self, on_gauge_requested, parent=None):
        super().__init__(parent)

        self.on_gauge_requested = on_gauge_requested

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["Timestamp", "Interface", "ID", "Data Len", "Name", "Data"])
        self.tree.setSortingEnabled(True)
        self.tree.sortItems(2, Qt.AscendingOrder)
        layout.addWidget(self.tree)

        self.tree.collapseAll()  # start collapsed

        self._ids_seen: defaultdict[int, dict] = defaultdict(dict)

    def add_row(self, timestamp: str, interface: str, id_: str, data_len: str, name: str, data: str, signals: dict):
        can_id = f"{id_:03X}"
        item = QTreeWidgetItem([timestamp, interface, can_id, data_len, name, data])
        self.tree.addTopLevelItem(item)

        # child item that holds the expanded custom widget area
        child = QTreeWidgetItem(item)
        item.addChild(child)
        self.tree.setFirstItemColumnSpanned(child, True)  # let it span all columns

        expand_widget = QWidget()
        expand_layout = QVBoxLayout(expand_widget)
        expand_layout.setAlignment(Qt.AlignLeft)

        # show the signals and a 'create gauge' button
        if signals:
            item.signal_labels = {}

            signals_form = QFormLayout()
            signals_form.setFormAlignment(Qt.AlignLeft)

            for key, value in signals.items():
                key_label = QLabel(f"{key}:")
                value_label = QLabel(format_signal_value(value))
                item.signal_labels[key] = value_label
                signals_form.addRow(key_label, value_label)

            expand_layout.addLayout(signals_form)

            # Create Gauge Button
            create_gauge_btn = QPushButton("Create Gauge")
            create_gauge_btn.clicked.connect(
                lambda checked, n=name, s=signals: self.on_click_create_gauge_btn(n, s)
            )
            expand_layout.addWidget(create_gauge_btn)
        else:
            decode_btn = QPushButton("Decode")
            # decode_btn.clicked.connect(lambda checked, i=id_: self.on_click_decode_btn(i, self._ids_seen))
            expand_layout.addWidget(decode_btn)

        self.tree.setItemWidget(child, 0, expand_widget)

        return item

    def on_click_create_gauge_btn(self, name, signals):
        self.gauge_creation_popup = CreateGaugePopup(self, name, signals, self.on_gauge_requested)
        self.gauge_creation_popup.exec()

    def on_click_decode_btn(self, id_, data):
        print("I ain't do this shit yet")

    def on_msgs(self, msgs: list[DecodedMsg]):

        self.setUpdatesEnabled(False)
        self.tree.setSortingEnabled(False)

        for msg in msgs:
            ts = format_time(msg.timestamp)
            channel = msg.channel
            dlc_str = f"[{msg.dlc}]"
            name = (msg.name or "").replace("_", " ")
            data = msg.raw_hex
            signals = msg.signals
        
            if msg.can_id in self._ids_seen.keys():
                self._ids_seen[msg.can_id]["data"] = msg
                # update pre-existing row elem, not all should change
                item = self._ids_seen[msg.can_id]["widget"]
                item.setText(0, ts)        # Timestamp
                item.setText(3, dlc_str)   # Data Len
                item.setText(5, data)      # Data

                for sig_name, value in signals.items():
                    if sig_name in item.signal_labels:
                        item.signal_labels[sig_name].setText(format_signal_value(value))
            else:
                self._ids_seen[msg.can_id]["data"] = msg
                item = self.add_row(ts, channel, msg.can_id, dlc_str, name, data, signals)
                self._ids_seen[msg.can_id]["widget"] = item
        
        self.tree.setSortingEnabled(True)
        self.setUpdatesEnabled(True)

import time
def format_time(timestamp):
    return time.strftime("%H:%M:%S", time.localtime(timestamp or time.time())) + f".{int((timestamp or 0) % 1 * 1000):03d}"

def format_signal_value(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    if hasattr(value, "name"):
        return str(value.name)
    return str(value)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    page = SeenMessagesTable()
    page.resize(700, 400)
    page.show()

    sys.exit(app.exec_())