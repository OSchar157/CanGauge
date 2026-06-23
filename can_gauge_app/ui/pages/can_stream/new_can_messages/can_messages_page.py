from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFormLayout
)
from PyQt5.QtCore import Qt
from decoding.decoder import DecodedMsg
from ui.pages.can_stream.new_can_messages.create_gauge_popup import CreateGaugePopup

class SeenMessagesTable(QWidget):
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

        self._ids_seen: dict[int, QTreeWidgetItem] = {}

    def add_row(self, timestamp: str, interface: str, id_: str, data_len: str, name: str, data: str, signals: dict):
        item = QTreeWidgetItem([timestamp, interface, id_, data_len, name, data])
        self.tree.addTopLevelItem(item)

        # child item that holds the expanded custom widget area
        child = QTreeWidgetItem(item)
        item.addChild(child)
        self.tree.setFirstItemColumnSpanned(child, True)  # let it span all columns

        expand_widget = QWidget()
        expand_layout = QVBoxLayout(expand_widget)

        item.signal_labels = {}

        if signals:
            signals_form = QFormLayout()
            signals_form.setFormAlignment(Qt.AlignLeft)

            for key, value in signals.items():
                key_label = QLabel(f"{key}:")
                value_label = QLabel(format_signal_value(value))
                item.signal_labels[key] = value_label
                signals_form.addRow(key_label, value_label)

            expand_layout.addLayout(signals_form)

        expand_layout.setAlignment(Qt.AlignLeft)

        # Create Gauge Button
        create_gauge_btn = QPushButton("Create Gauge")
        create_gauge_btn.clicked.connect(
            lambda checked, i=id_, n=name, s=signals: self.on_click_create_gauge_btn(i, n, s)
        )
        expand_layout.addWidget(create_gauge_btn)

        self.tree.setItemWidget(child, 0, expand_widget)

        return item

    def on_click_create_gauge_btn(self, id_, name, signals):
        self.popup = CreateGaugePopup(self, id_, name, signals, self.on_gauge_requested)
        self.popup.exec()

    def on_msg(self, msg: DecodedMsg):
        ts = time.strftime("%H:%M:%S", time.localtime(msg.timestamp)) + f".{int(msg.timestamp % 1 * 1000):03d}"
        channel = msg.channel
        can_id = f"{msg.can_id:03X}"
        dlc_str = f"[{msg.dlc}]"
        name = (msg.name or "").replace("_", " ")
        data = msg.raw_hex
        signals = msg.signals
    
        if msg.can_id in self._ids_seen:
            # update pre-existing row elem, not all should change
            item = self._ids_seen[msg.can_id]
            item.setText(0, ts)        # Timestamp
            item.setText(3, dlc_str)   # Data Len
            item.setText(5, data)      # Data

            for name, value in signals.items():
                if name in item.signal_labels:
                    item.signal_labels[name].setText(format_signal_value(value))
        else:
            item = self.add_row(ts, channel, can_id, dlc_str, name, data, signals)
            self._ids_seen[msg.can_id] = item


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