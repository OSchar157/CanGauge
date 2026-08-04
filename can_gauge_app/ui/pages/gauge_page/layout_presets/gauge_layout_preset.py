import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QApplication, QPushButton,
    QVBoxLayout, QHBoxLayout, QBoxLayout, QDialog,
)

from can import Message
from cantools.database import Database

from ui.pages.gauge_page.select_signal_popup import SelectSignalPopup
from ui.pages.gauge_page.layout_presets.gauge_template_box import GaugeTemplateBox
from ui.gauge_widgets.gauge import Gauge
from ui import gauge_widgets  # package of gauge classes; adjust if this isn't where it lives

import worker_manager

# gauges with bottom row of indicators
class GaugeLayoutPreset(QWidget):
    def __init__(self, can_db: Database, parent=None):
        super().__init__(parent)
        self.can_db = can_db

        master = QVBoxLayout()
        self.setLayout(master)

        self.config_layout = QHBoxLayout()
        master.addLayout(self.config_layout)

        self.gauges_layout = QVBoxLayout()

        master.addLayout(self.gauges_layout)

        self.select_signal_popup = None

        self.gauges: dict[int, dict[str, list[Gauge]]] = {}
        self.slots: dict[int, GaugeTemplateBox] = {}

        self._next_id = 0

        self.shell = None

    def add_gauge_template_box(self, layout: QBoxLayout, box_size: tuple[int, int], slot: int):
        gauge_template_box = GaugeTemplateBox()
        gauge_template_box.setFixedSize(box_size[0], box_size[1])
        gauge_template_box.slot = slot
        gauge_template_box.clicked.connect(lambda box=gauge_template_box: self.open_select_signal_popup(box))
        layout.addWidget(gauge_template_box)
        self.slots[slot] = gauge_template_box

    def open_select_signal_popup(self, gauge_template_box: GaugeTemplateBox):
        self.select_signal_popup = SelectSignalPopup(can_db=self.can_db)
        worker_manager.set_owner(self.select_signal_popup, self.select_signal_popup.on_msgs)

        if self.select_signal_popup.exec() == QDialog.Accepted:
            create_gauge_popup = self.select_signal_popup.create_gauge_popup

            can_id = create_gauge_popup.can_id
            signal_name = create_gauge_popup.signal_name
            gauge_type, gauge_args = create_gauge_popup.user_created_gauge

            self.add_gauge(gauge_template_box.slot, can_id, signal_name, gauge_type, gauge_args)

        worker_manager.set_owner(self, self.on_msgs)

    def add_gauge(self, slot: int, can_id: int, sig_name: str, gauge_type: type[Gauge], gauge_args: dict):
        box = self.slots[slot]

        new_gauge = gauge_type(**gauge_args)

        new_gauge._id = self._next_id
        self._next_id += 1

        self.gauges.setdefault(can_id, {}).setdefault(sig_name, []).append(new_gauge)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(new_gauge, 1)

        rm_btn = QPushButton("Remove")
        rm_btn.clicked.connect(lambda *_, s=slot: self.remove_gauge(s))
        layout.addWidget(rm_btn)

        container._gauge = new_gauge
        container._config = {
            "slot": slot,
            "can_id": can_id,
            "sig_name": sig_name,
            "gauge_type": gauge_type.__name__,
            "gauge_args": dict(gauge_args),
        }

        box.set_gauge(container)

    def remove_gauge(self, slot: int):
        box = self.slots[slot]
        container = box.gauge
        if container is None:
            return

        cfg = container._config
        gauge = container._gauge

        sig_gauges = self.gauges.get(cfg["can_id"], {}).get(cfg["sig_name"], [])
        if gauge in sig_gauges:
            sig_gauges.remove(gauge)

        # drop empty entries so on_msgs skips them entirely
        if not sig_gauges:
            self.gauges.get(cfg["can_id"], {}).pop(cfg["sig_name"], None)
            if not self.gauges.get(cfg["can_id"]):
                self.gauges.pop(cfg["can_id"], None)

        box.clear_gauge()

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

    def json(self) -> list[dict]:
        return [
            box.gauge._config
            for box in self.slots.values()
            if box.gauge is not None
        ]

    def load_gauges(self, configs: list[dict]):
        for cfg in configs:
            gauge_cls = getattr(gauge_widgets, cfg["gauge_type"], None)
            if gauge_cls is None:
                print(f"Unknown gauge type in save file: {cfg['gauge_type']}")
                continue

            slot = cfg["slot"]
            if slot not in self.slots:
                print(f"Unknown slot in save file: {slot}")
                continue

            self.add_gauge(slot, cfg["can_id"], cfg["sig_name"], gauge_cls, cfg["gauge_args"])

import sys
if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()
    db.add_dbc_string(open('subaru_global_TESTING.dbc').read())
    gauge_layout = GaugeLayoutPreset(db)
    gauge_layout.show()
    gauge_layout.showMaximized()
    sys.exit(app.exec_())