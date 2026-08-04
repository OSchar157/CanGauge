from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout,
    QPushButton, QHeaderView,
    QDialog, QHBoxLayout, QScroller
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from ui.pages.can_table.decode_id_popup import DecodeIdPopup
from ui.utils import format_timestamp, format_data

import worker_manager

from cantools.database import Database
from can import Message

COL_HEADERS = ["TIMESTAMP", "IFACE", "ID", "DLC", "NAME", "DATA"]
class CanTable(QWidget):
    def __init__(self, can_db: Database, parent=None):
        super().__init__(parent)

        self.can_db = can_db

        self.decode_id_popup = None
        self.create_gauge_popup = None

        self._current_sort_col = 2
        self._current_sort_order = Qt.AscendingOrder

        self._build_ui()

    def _build_ui(self):
        if self.layout() is not None:
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(COL_HEADERS))
        self.tree.setHeaderLabels(COL_HEADERS)
        self.tree.setSortingEnabled(False)
        self.tree.setIndentation(50)
        layout.addWidget(self.tree)

        table_header = self.tree.header()
        table_header.setSectionsClickable(True)
        table_header.sectionClicked.connect(self._manual_sort_table)

        font = self.tree.font()
        font.setPointSize(16)
        self.tree.setFont(font)

        self.tree.setStyleSheet("""
            QTreeWidget::item {
                padding: 12px 4px;
            }

            QScrollBar:vertical {
                width: 40px;
            }

            QScrollBar::handle:vertical {
                background: #808080;
                border-radius: 8px;
                min-height: 40px;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        col_widths = [175,65,60,50,250,300]
        for col in range(len(COL_HEADERS)):
            self.tree.setColumnWidth(col, col_widths[col])

        self.tree.collapseAll()

        self.can_ids_seen: dict[int, QWidget] = {}

    def configure_util_bar(self, util_bar_layout):
        pass
    
    def _manual_sort_table(self, col: int):
        if self._current_sort_col == col:
            if self._current_sort_order == Qt.AscendingOrder:
                self._current_sort_order = Qt.DescendingOrder
            else:
                self._current_sort_order = Qt.AscendingOrder
        else:
            self._current_sort_col = col
            self._current_sort_order = Qt.AscendingOrder

        table_header = self.tree.header()
        table_header.setSortIndicator(self._current_sort_col, self._current_sort_order)
        self.tree.sortItems(self._current_sort_col, self._current_sort_order)

    def add_row(self, raw_msg: Message, msg_name: str, id_is_decodable: bool):
        can_id = raw_msg.arbitration_id

        item = QTreeWidgetItem(["", str(raw_msg.channel), f"{can_id:02X}", str(raw_msg.dlc), msg_name, ""])
        self.tree.addTopLevelItem(item)

        if id_is_decodable:
            self._build_signals_section(item, raw_msg)
        else:
            self._add_decode_row(item, "Decode", raw_msg)

        self.can_ids_seen[can_id] = item

    def _build_signals_section(self, item: QTreeWidgetItem, raw_msg: Message):
        can_id = raw_msg.arbitration_id

        signal_items: dict[str, QTreeWidgetItem] = {}
        item.signal_items = signal_items

        signals = self.can_db.get_message_by_frame_id(can_id).signals

        for signal in signals:
            sig_item = QTreeWidgetItem(item, ["", "", "", "", signal.name, ""])
            signal_items[signal.name] = sig_item

        self._add_decode_row(item, "Edit Decoding", raw_msg)

    def _add_decode_row(self, item: QTreeWidgetItem, btn_name: str, raw_msg: Message):
        btn_child = QTreeWidgetItem(item)
        self.tree.setFirstItemColumnSpanned(btn_child, True)

        container = QWidget()
        btn_layout = QHBoxLayout(container)
        btn_layout.setContentsMargins(8, 4, 8, 40)
        btn_layout.setAlignment(Qt.AlignCenter)

        btn = QPushButton(btn_name)
        btn.setMinimumWidth(160)
        btn.setFixedHeight(45)
        btn.clicked.connect(lambda checked, m=raw_msg: self.on_click_decode_btn(m))
        btn_layout.addWidget(btn)

        self.tree.setItemWidget(btn_child, 0, container)

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

            signal_items = item.signal_items
            for sig_name, sig_val in decoded_msg_signals.items():
                if sig_name in signal_items:
                    signal_items[sig_name].setText(5, fmt_sig(sig_val))

        self.tree.setUpdatesEnabled(True)

def format_signal_value(value):
    if isinstance(value, float):
        return f"{value:.3f}"
    if hasattr(value, "name"):
        return str(value.name)
    return str(value)