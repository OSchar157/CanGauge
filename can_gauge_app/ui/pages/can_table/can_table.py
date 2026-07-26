from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFormLayout, QHeaderView,
    QDialog, QHBoxLayout, QScroller
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from ui.pages.can_table.decode_id_popup import DecodeIdPopup
from ui.utils import format_timestamp, format_data

import worker_manager

from cantools.database import Database
from can import Message

class CanTable(QWidget):
    def __init__(self, on_gauge_requested, can_db: Database, parent=None):
        super().__init__(parent)

        self.on_gauge_requested = on_gauge_requested
        self.can_db = can_db

        self.decode_id_popup = None
        self.create_gauge_popup = None

        self._current_sort_col = 2  # Default to ID column matching your initial setup
        self._current_sort_order = Qt.AscendingOrder

        self._build_ui()

    def _build_ui(self):
        if self.layout() is not None:
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["Timestamp", "Interface", "ID", "Data Len", "Name", "Data"])
        self.tree.setSortingEnabled(False)
        layout.addWidget(self.tree)

        table_header = self.tree.header()
        table_header.setSectionsClickable(True)
        table_header.sectionClicked.connect(self._manual_sort_table)

        self.tree.collapseAll()

        self.can_ids_seen: dict[int, QWidget] = {}

    def _manual_sort_table(self, col: int):
        # 1. Flip order if clicking the same column, otherwise default to Ascending
        if self._current_sort_col == col:
            if self._current_sort_order == Qt.AscendingOrder:
                self._current_sort_order = Qt.DescendingOrder
            else:
                self._current_sort_order = Qt.AscendingOrder
        else:
            self._current_sort_col = col
            self._current_sort_order = Qt.AscendingOrder
            
        # 2. Force the header triangle icon to match your tracked state
        table_header = self.tree.header()
        table_header.setSortIndicator(self._current_sort_col, self._current_sort_order)
        
        # 3. Fire the single manual sort execution pass
        self.tree.sortItems(self._current_sort_col, self._current_sort_order)

    def add_row(self, raw_msg: Message, msg_name: str, id_is_decodable: bool):
        can_id = raw_msg.arbitration_id

        item = QTreeWidgetItem(["", str(raw_msg.channel), f"{can_id:02X}", str(raw_msg.dlc), msg_name, ""])
        self.tree.addTopLevelItem(item)

        # child item that holds the expanded custom widget area
        child = QTreeWidgetItem(item)
        item.addChild(child)
        self.tree.setFirstItemColumnSpanned(child, True)

        expand_widget = QWidget()
        expand_layout = QVBoxLayout(expand_widget)
        expand_layout.setAlignment(Qt.AlignLeft)

        if id_is_decodable:
            self._build_signals_section(item, expand_layout, raw_msg)
        else:
            self._add_decode_btn("Decode", expand_layout, raw_msg)

        self.tree.setItemWidget(child, 0, expand_widget)

        self.can_ids_seen[can_id] = item
    
    def _build_signals_section(self, item: QTreeWidgetItem, layout: QVBoxLayout, raw_msg: Message):
        can_id = raw_msg.arbitration_id

        signal_labels: dict[str, QLabel] = {}
        item.signal_labels = signal_labels

        signals_form = QFormLayout()
        signals_form.setFormAlignment(Qt.AlignLeft)

        signals = self.can_db.get_message_by_frame_id(can_id).signals

        for signal in signals:
            sig_name = signal.name
            sig_name_label = QLabel(f"{sig_name}:")
            value_label = QLabel("")
            item.signal_labels[sig_name] = value_label
            signals_form.addRow(sig_name_label, value_label)

        layout.addLayout(signals_form)

        btn_layout = QHBoxLayout()

        self._add_decode_btn("Edit Decoding", btn_layout, raw_msg)

        layout.addLayout(btn_layout)

    def _add_decode_btn(self, btn_name: str, layout: QVBoxLayout, msg: Message):
        btn = QPushButton(btn_name)
        btn.clicked.connect(lambda checked, m=msg: self.on_click_decode_btn(m))
        layout.addWidget(btn)

    def on_click_decode_btn(self, raw_msg: Message):
        self.decode_id_popup = DecodeIdPopup(raw_msg=raw_msg, can_db=self.can_db)
        worker_manager.set_owner(self.decode_id_popup, self.decode_id_popup.on_msgs)

        if self.decode_id_popup.exec_() == QDialog.Accepted:
            self.decode_id_popup = None
            self._build_ui()
        
        worker_manager.set_owner(self, self.on_msgs)

    def on_click_edit_encoding_btn(self, msg: Message):
        self.decode_id_popup = DecodeIdPopup(msg=msg, can_db=self.can_db)

    def on_msgs(self, msgs: list[Message]):
        can_ids_to_update = set(msg.arbitration_id for msg in msgs)
        new_can_ids = can_ids_to_update.difference(self.can_ids_seen)

        self.tree.setUpdatesEnabled(False)

        db_get_msg = self.can_db.get_message_by_frame_id
        fmt_ts = format_timestamp
        fmt_data = format_data
        fmt_sig = format_signal_value
        ids_seen = self.can_ids_seen

        for msg in reversed(msgs):
            if not can_ids_to_update:
                break

            can_id = msg.arbitration_id
            if can_id not in can_ids_to_update:
                continue

            try:
                db_msg = db_get_msg(can_id)
                decoded_msg_signals = db_msg.decode(msg.data)
                msg_name = db_msg.name
                is_decodable = True
            except KeyError:
                msg_name = ""
                is_decodable = False

            if can_id in new_can_ids:
                self.add_row(msg, msg_name, is_decodable)

            item = ids_seen[can_id]
            item.setText(0, fmt_ts(msg.timestamp))
            item.setText(5, fmt_data(msg.data))

            can_ids_to_update.discard(can_id)

            if not is_decodable:
                continue

            signal_labels = item.signal_labels
            for sig_name, sig_val in decoded_msg_signals.items():
                if sig_name in signal_labels:
                    signal_labels[sig_name].setText(fmt_sig(sig_val))
    
        self.tree.setUpdatesEnabled(True)

def format_signal_value(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    if hasattr(value, "name"):
        return str(value.name)
    return str(value)