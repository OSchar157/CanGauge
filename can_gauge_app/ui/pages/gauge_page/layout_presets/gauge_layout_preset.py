import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QApplication, QPushButton,
    QVBoxLayout, QHBoxLayout, QBoxLayout, QDialog,
    QFrame
)
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, pyqtSignal

from can import Message
from cantools.database import Database

from ui.pages.gauge_page.select_signal_popup import SelectSignalPopup
from ui.gauge_widgets.gauge import Gauge
from ui import gauge_widgets  # package of gauge classes; adjust if this isn't where it lives

import worker_manager

# saved next to this file; change if you want it elsewhere
SAVE_FILE = Path(__file__).with_name("gauge_layout.json")

class GaugeTemplateBox(QFrame):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            GaugeTemplateBox {
                border: 4px dashed #808080;
                border-radius: 16px;
                background: transparent;
            }

            GaugeTemplateBox:hover {
                border-color: #4da3ff;
                background: rgba(77,163,255,20);
            }
        """)

        self.slot = None
        self.gauge = None

        self._layout = QVBoxLayout(self)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self.gauge is not None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor("#808080"), 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        s = 16  # half-length of plus
        c = self.rect().center()

        painter.drawLine(c.x() - s, c.y(), c.x() + s, c.y())
        painter.drawLine(c.x(), c.y() - s, c.x(), c.y() + s)

    def mousePressEvent(self, event):
        if self.gauge is not None:
            return
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

    def set_gauge(self, gauge: QWidget):
        self.gauge = gauge
        self._layout.addWidget(gauge)
        self.update()

    def clear_gauge(self):
        """Undo set_gauge(): tear the widget back out and show the '+' placeholder again."""
        if self.gauge is None:
            return
        self._layout.removeWidget(self.gauge)
        self.gauge.setParent(None)
        self.gauge.deleteLater()
        self.gauge = None
        self.update()


NUM_GAUGES_PER_ROW = 3
# gauges with bottom row of indicators
class GaugeLayoutPreset(QWidget):
    def __init__(self, can_db: Database, parent=None):
        super().__init__(parent)
        self.can_db = can_db

        master = QVBoxLayout()
        self.setLayout(master)

        self.config_layout = QHBoxLayout()
        master.addLayout(self.config_layout)

        all_gauges_layout = QVBoxLayout()

        self.gauges_1_layout = QHBoxLayout()
        self.gauges_2_layout = QHBoxLayout()

        all_gauges_layout.addLayout(self.gauges_1_layout)
        all_gauges_layout.addLayout(self.gauges_2_layout)

        master.addLayout(all_gauges_layout)

        self.select_signal_popup = None

        self.gauges: dict[int, dict[str, list[Gauge]]] = {}
        self.slots: dict[int, GaugeTemplateBox] = {}

        self._next_id = 0

        self.shell = None

        for i in range(NUM_GAUGES_PER_ROW):
            self.add_gauge_template_box(self.gauges_1_layout, slot=i)
            self.add_gauge_template_box(self.gauges_2_layout, slot=i + NUM_GAUGES_PER_ROW)

        self.load_gauges()

    def add_gauge_template_box(self, layout: QBoxLayout, slot: int):
        gauge_template_box = GaugeTemplateBox()
        gauge_template_box.slot = slot
        gauge_template_box.clicked.connect(lambda box=gauge_template_box: self.open_select_signal_popup(box))
        layout.addWidget(gauge_template_box)
        self.slots[slot] = gauge_template_box

    def open_select_signal_popup(self, gauge_template_box: GaugeTemplateBox):
        self.select_signal_popup = SelectSignalPopup(can_db=self.can_db, parent=self)
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

    def save_gauges(self):
        configs = [
            box.gauge._config
            for box in self.slots.values()
            if box.gauge is not None
        ]
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(configs, f, indent=2)
        except (OSError, TypeError) as e:
            # TypeError = something in gauge_args wasn't JSON-serializable
            print(f"Failed to save gauges: {e}")

    def load_gauges(self):
        if not SAVE_FILE.exists():
            return

        try:
            with open(SAVE_FILE) as f:
                configs = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Failed to load gauges: {e}")
            return

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