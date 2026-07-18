from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFormLayout, QHeaderView,
    QDialog, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from ui.pages.can_table.create_gauge_popup import CreateGaugePopup
from ui.pages.can_table.decode_id_popup import DecodeIdPopup
from ui.utils import format_timestamp, format_data

from cantools.database import Database
from can import Message

class CanTable(QWidget):
    def __init__(self, on_gauge_requested, can_db: Database, parent=None):
        super().__init__(parent)

        self.shell = None

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
        # self.tree.sortItems(2, Qt.AscendingOrder)
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
            self._build_signals_section(item, expand_layout, can_id)
        else:
            self._build_decode_section(expand_layout, raw_msg)

        self.tree.setItemWidget(child, 0, expand_widget)

        self.can_ids_seen[can_id] = item
    
    def _build_signals_section(self, item: QTreeWidgetItem, layout: QVBoxLayout, can_id: int):
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

        create_gauge_btn = QPushButton("Create Gauge")
        can_msg_name = self.can_db.get_message_by_frame_id(can_id).name
        signal_names = [signal.name for signal in signals]
        create_gauge_btn.clicked.connect(
            lambda checked,i=can_id, n=can_msg_name, s=signal_names: self.on_click_create_gauge_btn(i, n, s)
        )
        btn_layout.addWidget(create_gauge_btn)

        edit_encoding_btn = QPushButton("Edit Encoding")
        edit_encoding_btn.clicked.connect(self.on_click_edit_encoding_btn)
        btn_layout.addWidget(edit_encoding_btn)

        layout.addLayout(btn_layout)

    def _build_decode_section(self, layout: QVBoxLayout, msg: Message):
        decode_btn = QPushButton("Decode")
        decode_btn.clicked.connect(lambda checked, m=msg: self.on_click_decode_btn(m))
        layout.addWidget(decode_btn)
        
    def on_click_create_gauge_btn(self, can_id, can_msg_name, signal_names):
        self.create_gauge_popup = CreateGaugePopup(self, can_id, can_msg_name, signal_names, self.on_gauge_requested)
        self.create_gauge_popup.exec()

    def on_click_decode_btn(self, msg: Message):
        self.decode_id_popup = DecodeIdPopup(can_id=msg.arbitration_id, data_len=msg.dlc,
                                             is_extended=msg.is_extended_id, can_db=self.can_db)
        self.shell.worker.msg_buffer_emitter.connect(self.decode_id_popup.on_msgs)

        if self.decode_id_popup.exec_() == QDialog.Accepted:
            self.shell.worker.msg_buffer_emitter.disconnect(self.decode_id_popup.on_msgs)
            self.decode_id_popup = None
            self._build_ui()

    def on_click_edit_encoding_btn(self, msg: Message):
        pass

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