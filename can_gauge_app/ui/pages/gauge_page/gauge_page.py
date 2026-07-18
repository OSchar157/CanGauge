import sys, json

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QApplication, QPushButton,
    QVBoxLayout
)

from ...gauge_widgets import Gauge

from can import Message
from cantools.database import Database


class GaugePage(QWidget):
    def __init__(self, can_db: Database):
        super().__init__()

        self.shell = None
        
        self.can_db = can_db

        master = QVBoxLayout()
        self.setLayout(master)

        self.gauges_layout = QHBoxLayout()
        master.addLayout(self.gauges_layout)

        self.gauges: dict[int, dict[str, list[Gauge]]] = {}

        self._next_id = 0

    def on_msgs(self, msgs: list[Message]):
        if not self.gauges:
            return

        ids_to_update = set(self.gauges.keys())
        for msg in reversed(msgs):
            if not ids_to_update:
                break
            
            can_id = msg.arbitration_id

            if can_id not in ids_to_update:
                continue
            
            decoded_msg_signals = self.can_db.decode_message(can_id, msg.data)

            for sig_name, sig_value in decoded_msg_signals.items():
                if sig_name not in self.gauges[can_id]:
                    continue
                for gauge in self.gauges[can_id][sig_name]:
                        gauge.set_value(sig_value)
                    
                ids_to_update.discard(can_id)

    def add_gauge(self, can_id: int, sig_name: str, gauge_type: Gauge, gauge_args: dict):
        new_gauge = gauge_type(**gauge_args)
        
        new_gauge._id = self._next_id
        self._next_id += 1

        if can_id not in self.gauges:
            self.gauges[can_id] = {}
        
        if sig_name not in self.gauges[can_id]:
            self.gauges[can_id][sig_name] = []

        self.gauges[can_id][sig_name].append(new_gauge)

        layout = QVBoxLayout()
        layout.addWidget(new_gauge)

        rm_gauge_btn = RemoveGaugeBtn(layout, new_gauge, parent=self)
        layout.addWidget(rm_gauge_btn)

        self.gauges_layout.addLayout(layout)

class RemoveGaugeBtn(QPushButton):
    def __init__(self, layout, gauge, parent: GaugePage):
        super().__init__(parent, text="Remove")
        self.parent = parent
        self.gauge_layout = layout
        self.gauge = gauge
        self.clicked.connect(self.rm_layout)

    def rm_layout(self):
        while self.gauge_layout.count():
            item = self.gauge_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        self.parent.gauges_layout.removeItem(self.gauge_layout)
        self.gauge_layout.deleteLater()

        for gauges in self.parent.gauges.values():
            if self.gauge in gauges:
                gauges.remove(self.gauge)
                break

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GaugePage()
    window.show()
    sys.exit(app.exec_())