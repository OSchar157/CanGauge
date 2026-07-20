import sys
import json
import math
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QApplication, QPushButton,
    QVBoxLayout
)

from PyQt5.QtCore import Qt

from ... import gauge_widgets
from ...gauge_widgets import Gauge

from can import Message
from cantools.database import Database

# saved next to this file; change if you want it elsewhere
SAVE_FILE = Path(__file__).with_name("gauges.json")

class GaugePage(QWidget):
    def __init__(self, can_db: Database):
        super().__init__()

        self.shell = None

        self.can_db = can_db

        master = QVBoxLayout()
        self.setLayout(master)

        self.gauges_layout = QGridLayout()
        master.addLayout(self.gauges_layout, 1)  # stretch=1 -> grid gets all the space

        # fast lookup for on_msgs: can_id -> sig_name -> [Gauge, ...]
        self.gauges: dict[int, dict[str, list[Gauge]]] = {}

        # one container widget (gauge + remove button) per gauge, in the
        # order they were added. drives both the tiling and the save file.
        self._containers: list[QWidget] = []

        self._next_id = 0

        self.load_gauges()

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

    def add_gauge(self, can_id: int, sig_name: str, gauge_type: type[Gauge], gauge_args: dict):
        new_gauge = gauge_type(**gauge_args)

        new_gauge._id = self._next_id
        self._next_id += 1

        self.gauges.setdefault(can_id, {}).setdefault(sig_name, []).append(new_gauge)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(new_gauge, 1)

        rm_btn = QPushButton("Remove")
        rm_btn.clicked.connect(lambda *_, c=container: self.remove_gauge(c))
        layout.addWidget(rm_btn)

        # everything needed to recreate this gauge later
        container._gauge = new_gauge
        container._config = {
            "can_id": can_id,
            "sig_name": sig_name,
            "gauge_type": gauge_type.__name__,
            "gauge_args": dict(gauge_args),
        }

        self._containers.append(container)
        self._relayout()

    def remove_gauge(self, container: QWidget):
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

        if container in self._containers:
            self._containers.remove(container)

        self.gauges_layout.removeWidget(container)
        container.setParent(None)
        container.deleteLater()

        self._relayout()

    def _relayout(self):
        """Re-tile all gauges into a roughly square grid.

        1 gauge -> fills the page, 2 -> side by side, 3-4 -> 2x2,
        5-9 -> 3x3, etc. Position follows the order gauges were added.
        """
        # detach everything (widgets stay alive, they just get re-placed)
        while self.gauges_layout.count():
            self.gauges_layout.takeAt(0)

        # reset stretch left over from a previously bigger grid
        for c in range(self.gauges_layout.columnCount()):
            self.gauges_layout.setColumnStretch(c, 0)
        for r in range(self.gauges_layout.rowCount()):
            self.gauges_layout.setRowStretch(r, 0)

        n = len(self._containers)
        if n == 0:
            return

        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        for i, container in enumerate(self._containers):
            row, col = divmod(i, cols)
            self.gauges_layout.addWidget(container, row, col)

        # make all cells share the space evenly
        for c in range(cols):
            self.gauges_layout.setColumnStretch(c, 1)
        for r in range(rows):
            self.gauges_layout.setRowStretch(r, 1)

    def save_gauges(self):
        configs = [c._config for c in self._containers]
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
            self.add_gauge(cfg["can_id"], cfg["sig_name"], gauge_cls, cfg["gauge_args"])


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = GaugePage()
    window.show()
    sys.exit(app.exec_())