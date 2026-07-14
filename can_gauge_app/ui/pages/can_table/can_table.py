from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFormLayout, QHeaderView,
    QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from can_worker.worker import DecodedMsg
from ui.pages.can_table.create_gauge_popup import CreateGaugePopup
from collections import defaultdict
from ui.pages.can_table.decode_id_popup import DecodeIdPopup

from cantools.database import Database

class CanTable(QWidget):
    new_frame = pyqtSignal(object)

    def __init__(self, on_gauge_requested, db: Database, parent=None):
        super().__init__(parent)

        self.on_gauge_requested = on_gauge_requested
        self.db = db

        self._build_ui()

    def _build_ui(self):
        if self.layout() is not None:
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["Timestamp", "Interface", "ID", "Data Len", "Name", "Data"])
        self.tree.setSortingEnabled(True)
        self.tree.sortItems(2, Qt.AscendingOrder)
        layout.addWidget(self.tree)

        self.tree.collapseAll()  # start collapsed

        self._ids_seen = {}   # can_id -> {"data": DecodedMsg, "widget": QTreeWidgetItem}
        self._pending = {}    # can_id -> newest DecodedMsg since last flush
    
        self._ui_timer = QTimer(self)
        self._ui_timer.setInterval(50)      # 20 fps; bump to 100 ms if you want
        self._ui_timer.timeout.connect(self._flush_pending)
        self._ui_timer.start()
    
        self.tree.itemExpanded.connect(self._on_item_expanded)
    
        # 1) Sorting is OFF permanently while streaming. We only sort when the
        #    user clicks a header (and when a brand-new id appears, to keep
        #    their chosen order valid -- rare after startup).
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder
        self.tree.setSortingEnabled(False)
        header = self.tree.header()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.sectionClicked.connect(self._on_header_clicked)
    
        # 2) If any column used ResizeToContents, every setText forced the header
        #    to re-measure that column across all rows. Interactive + a one-time
        #    measure at startup avoids that entirely.
        header.setSectionResizeMode(QHeaderView.Interactive)
        for col in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(col)

    def add_row(self, timestamp: str, interface: str, id_: str, data_len: str, name: str, data: str, signals: dict, is_extended: bool):
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
            decode_btn.clicked.connect(lambda checked, i=can_id, d=data_len[1:-1], e=is_extended, db=self.db: self.on_click_decode_btn(i, d, e, db))
            expand_layout.addWidget(decode_btn)

        self.tree.setItemWidget(child, 0, expand_widget)

        return item

    def on_click_create_gauge_btn(self, name, signals):
        self.gauge_creation_popup = CreateGaugePopup(self, name, signals, self.on_gauge_requested)
        self.gauge_creation_popup.exec()

    def on_click_decode_btn(self, can_id, data_len, is_extended, db):
        self.decode_id_popup = DecodeIdPopup(can_id, data_len, is_extended, db, parent=self)
        self.new_frame.connect(self.decode_id_popup.on_new_frame)

        if self.decode_id_popup.exec_() == QDialog.Accepted:
            self.new_frame.disconnect(self.decode_id_popup.on_new_frame)
            self.decode_id_popup = None
            self._build_ui()

    # --- ingest: called for every incoming batch, does NO UI work ---------------
    def _on_header_clicked(self, col):
        if col == self._sort_column:
            self._sort_order = (
                Qt.DescendingOrder
                if self._sort_order == Qt.AscendingOrder
                else Qt.AscendingOrder
            )
        else:
            self._sort_column = col
            self._sort_order = Qt.AscendingOrder
        self.tree.sortItems(col, self._sort_order)
        self.tree.header().setSortIndicator(col, self._sort_order)
    
    # --- ingest -------------------------------------------------------------------
    def on_msgs(self, msgs):
        for msg in msgs:
            self._pending[msg.can_id] = msg   # coalesce: newest per id wins
        self.new_frame.emit(msgs)
    
    # --- render (at most 20x/sec) ---------------------------------------------
    def _flush_pending(self):
        if not self._pending:
            return
        pending, self._pending = self._pending, {}
    
        # No setUpdatesEnabled / setSortingEnabled toggling anymore. With ~50
        # rows, letting Qt repaint just the changed cells is cheaper than
        # forcing a full-tree repaint every flush.
        new_rows = False
        for can_id, msg in pending.items():
            entry = self._ids_seen.get(can_id)
            if entry is None:
                item = self.add_row(
                    format_time(msg.timestamp),
                    msg.channel,
                    can_id,
                    f"[{msg.data_len}]",
                    (msg.name or "").replace("_", " "),
                    msg.raw_hex,
                    msg.signals,
                    msg.is_extended,
                )
                item.can_id = can_id
                self._ids_seen[can_id] = {"data": msg, "widget": item}
                new_rows = True
            else:
                entry["data"] = msg
                item = entry["widget"]
                item.setText(0, format_time(msg.timestamp))
                item.setText(3, f"[{msg.data_len}]")
                item.setText(5, msg.raw_hex)
                if item.isExpanded():
                    self._refresh_signal_labels(item, msg.signals)
    
        # Keep the user's chosen sort valid when a new id shows up.
        if new_rows and self._sort_column >= 0:
            self.tree.sortItems(self._sort_column, self._sort_order)
    
    
    def _refresh_signal_labels(self, item, signals):
        labels = getattr(item, "signal_labels", None)
        if not labels:
            return
        for sig_name, value in signals.items():
            label = labels.get(sig_name)
            if label is not None:
                label.setText(format_signal_value(value))
    
    def _on_item_expanded(self, item):
        entry = self._ids_seen.get(getattr(item, "can_id", None))
        if entry is not None:
            self._refresh_signal_labels(item, entry["data"].signals)
    
import time
def format_time(timestamp):
    return time.strftime("%H:%M:%S", time.localtime(timestamp or time.time())) + f".{int((timestamp or 0) % 1 * 1000):03d}"

def format_signal_value(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    if hasattr(value, "name"):
        return str(value.name)
    return str(value)