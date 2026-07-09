import sys, json

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QApplication, QPushButton,
    QVBoxLayout
)

from ...gauge_widgets import Gauge

from can_worker.worker import DecodedMsg


class GaugePage(QWidget):
    def __init__(self):
        super().__init__()

        master = QVBoxLayout()
        # master.addStretch()
        self.setLayout(master)

        self.gauges_layout = QHBoxLayout()
        master.addLayout(self.gauges_layout)

        # self.save_btn = QPushButton("Save Gauges")
        # self.save_btn.clicked.connect(self._on_clicked_save)
        # self.save_btn.setVisible(False)
        # master.addWidget(self.save_btn)

        self.gauges: dict[str, list[Gauge]] = {}
        self.able_to_save = False

        self._next_id = 0

    def on_msgs(self, msgs):
        if not self.gauges:
            return

        remaining = set(self.gauges.keys())

        for msg in reversed(msgs):
            if not remaining:
                break
            for name, value in msg.signals.items():
                if name in remaining:
                    for gauge in self.gauges[name]:
                        try:
                            gauge.set_value(value)
                        except:
                            print(name, value)
                    remaining.discard(name)
    
    def add_gauge(self, gauge_type: Gauge, name: str, args):
        # self.save_btn.setVisible(True)
        
        new_gauge = gauge_type(**args)
        
        new_gauge._id = self._next_id
        self._next_id += 1

        if name not in self.gauges:
            self.gauges[name] = []
        
        self.gauges[name].append(new_gauge)

        layout = QVBoxLayout()
        layout.addWidget(new_gauge)

        rm_gauge_btn = RemoveGaugeBtn(layout, new_gauge, parent=self)
        layout.addWidget(rm_gauge_btn)

        self.gauges_layout.addLayout(layout)
        self.able_to_save = True

    def _on_clicked_save(self):
        if not (self.gauges and self.able_to_save):
            return
        
        gauges_jsons: list[dict] = []

        for name, gauges in self.gauges.items():
            for gauge in gauges:
                gauge_json = gauge.to_json()
                gauge_json["id_name"] = name
                gauges_jsons.append(gauge_json)
        
        self.able_to_save = False

        print(gauges_jsons)
        with open("gauges.json", "w") as f:
            json.dump(gauges_jsons, f, indent=2)

class RemoveGaugeBtn(QPushButton):
    def __init__(self, layout, gauge, parent: GaugePage):
        super().__init__(parent, text="Remove")
        self.parent = parent
        self.layout = layout
        self.gauge = gauge
        self.clicked.connect(self.rm_layout)

    def rm_layout(self):
        # Remove and delete every widget/item from the layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            else:
                # handle nested layouts if any
                sub_layout = item.layout()
                if sub_layout is not None:
                    self._clear_layout(sub_layout)

        # remove the gauge from the dict
        for gauges in self.parent.gauges.values():
            for gauge in gauges:
                if gauge._id == self.gauge._id:
                    gauges.remove(gauge)
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