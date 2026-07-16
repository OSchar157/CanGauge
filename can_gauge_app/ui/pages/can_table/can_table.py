from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QPushButton, QLabel, QFormLayout, QHeaderView,
    QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from ui.pages.can_table.create_gauge_popup import CreateGaugePopup
from ui.pages.can_table.decode_id_popup import DecodeIdPopup
from ui.utils import format_timestamp, get_data_for_gui

from cantools.database import Database
from can import Message

class CanTable(QWidget):
    def __init__(self, on_gauge_requested, can_db: Database, parent=None):
        super().__init__(parent)

        self.on_gauge_requested = on_gauge_requested
        self.can_db = can_db

        temp_decode_ppopup = DecodeIdPopup()
        self.decode_id_popup = temp_decode_ppopup

        self.create_gauge_popup = None

        self.recv_msgs: bool = False

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

        self.tree.collapseAll()

        self.can_ids_seen: dict[int, QWidget] = {}

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

        create_gauge_btn = QPushButton("Create Gauge")

        can_msg_name = self.can_db.get_message_by_frame_id(can_id).name
        signal_names = [signal.name for signal in signals]

        create_gauge_btn.clicked.connect(
            lambda checked,i=can_id, n=can_msg_name, s=signal_names: self.on_click_create_gauge_btn(i, n, s)
        )

        layout.addWidget(create_gauge_btn)

    def _build_decode_section(self, layout: QVBoxLayout, msg: Message):
        decode_btn = QPushButton("Decode")
        decode_btn.clicked.connect(lambda checked, m=msg: self.on_click_decode_btn(m))
        layout.addWidget(decode_btn)
        
    def on_click_create_gauge_btn(self, can_id, can_msg_name, signal_names):
        self.create_gauge_popup = CreateGaugePopup(self, can_id, can_msg_name, signal_names, self.on_gauge_requested)
        self.create_gauge_popup.exec()

    def on_click_decode_btn(self, msg: Message):
        self.decode_id_popup.can_id = msg.arbitration_id
        self.decode_id_popup.data_len = msg.dlc
        self.decode_id_popup.is_extended_id = msg.is_extended_id
        self.decode_id_popup.can_db = self.can_db
        self.decode_id_popup.recv_msgs = True
        self.decode_id_popup.build_ui()

        if self.decode_id_popup.exec_() == QDialog.Accepted:
            self.decode_id_popup.destroy_ui()
            self._build_ui()

    def on_msgs(self, msgs: list[Message]):
        if not self.recv_msgs:
            return
        
        can_ids_to_update = set(msg.arbitration_id for msg in msgs)
        new_can_ids = can_ids_to_update.difference(self.can_ids_seen)

        self.setUpdatesEnabled(False)
        self.tree.setSortingEnabled(False)

        for msg in reversed(msgs):
            if not can_ids_to_update:
                break

            can_id = msg.arbitration_id
            if can_id not in can_ids_to_update:
                continue

            try:
                decoded_msg_signals = self.can_db.decode_message(can_id, msg.data)
                msg_name = self.can_db.get_message_by_frame_id(can_id).name
                is_decodable = True
            except KeyError:
                msg_name = ""
                is_decodable = False

            if can_id in new_can_ids:
                self.add_row(msg, msg_name, is_decodable)

            ts, _, _, _, data = get_data_for_gui(msg)
        
            item = self.can_ids_seen[can_id]
            item.setText(0, ts)
            item.setText(5, data)

            can_ids_to_update.discard(can_id)

            if not is_decodable:
                continue

            for sig_name, sig_val in decoded_msg_signals.items():
                if sig_name in item.signal_labels:
                    item.signal_labels[sig_name].setText(format_signal_value(sig_val))
    
        self.tree.setSortingEnabled(True)
        self.setUpdatesEnabled(True)


def format_signal_value(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    if hasattr(value, "name"):
        return str(value.name)
    return str(value)