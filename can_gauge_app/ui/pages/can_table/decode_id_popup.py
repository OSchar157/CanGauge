import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog,
    QHBoxLayout, QBoxLayout, QTableWidget, QHeaderView,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator

from cantools.database import Message, Signal, Database, Message
from cantools.database.conversion import BaseConversion
from cantools.database.can.signal import NamedSignalValue

MIN_SIGNAL_ROWS = 1

ORDER_OPTS = ["Little Endian", "Big Endian"]
TYPE_OPTS = ["Signed", "Unsigned"]

SIGNAL_HEADERS = [
            "Name", "Type", "Order", "Start Bit", "Length",
            "Scale", "Offset", "Min", "Max", "Unit", "Value"
            ]

class DecodeIdPopup(QDialog):
    def __init__(self, can_id: int=None, data_len: int=None, is_extended: bool=False, can_db=None, parent=None):
        super().__init__(parent)
        self.can_id = can_id
        self.data_len = data_len
        self.is_extended = is_extended
        self.can_db = can_db

        self.recv_msgs = False
    
    def build_ui(self):
        self.setWindowTitle(f"Decode CAN ID: {self.can_id}")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.addWidget(QLabel("Can Message:"))

        self._init_can_message_table()
        self._init_can_signals_table()

        btn_layout = QVBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._on_click_save_btn)
        btn_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        self.main_layout.addLayout(btn_layout)

    def destroy_ui(self):
        self.recv_msgs = False
        self.main_layout = None
    
    def _get_signal_from_table_row(self, row: int, is_test: bool):
        for col in range(self.signals_table.columnCount()):
            widget = self.signals_table.cellWidget(row, col)

            if isinstance(widget, QComboBox):
                text = widget.currentText()
            elif isinstance(widget, QLineEdit):
                text = widget.text()
            
            col_header = self.signals_table.horizontalHeaderItem(col).text()

            if not is_test:
                if widget is None or text == "":
                    QMessageBox.critical(None, "Error", "Ayy cuh you done f'ed up. You ain't done filled e'rthing out.")
                    return

            if col_header == "Name":
                name = text
            elif col_header == "Type":
                is_signed = (text == TYPE_OPTS[0])
            elif col_header == "Order":
                byte_order = "little_endian" if text == ORDER_OPTS[0] else "big_endian"
            elif col_header == "Start Bit":
                start = int(text)
            elif col_header == "Length":
                length = int(text)
            elif col_header == "Scale":
                print(text == "")
                if is_test and text == "":
                    text = "1"
                scale = float(text)
            elif col_header == "Offset":
                if is_test and text == "":
                    text = "0"
                offset = float(text)
            elif col_header == "Min":
                if is_test and text == "":
                    minimum = text = "0"
                minimum = float(text)
            elif col_header == "Max":
                if is_test and text == "":
                    text = "1"
                maximum = float(text)
            elif col_header == "Unit":
                unit = text
        
        conversion = BaseConversion.factory(scale=scale, offset=offset, is_float=False)
        signal = Signal(name=name,
                        start=start,
                        length=length,
                        conversion=conversion,
                        byte_order=byte_order,
                        is_signed=is_signed,
                        minimum=minimum,
                        maximum=maximum,
                        unit=unit
                    )
        return signal

    def _on_click_save_btn(self):
        new_signals = []
        for row in range(self.signals_table.rowCount()):
            signal = self._get_signal_from_table_row(row, is_test=False)
            new_signals.append(signal)

        new_message = Message(
            frame_id= self.can_id,
            name=self.name_line_edit.text(),
            length=self.data_len,
            signals=new_signals,
            is_extended_frame=False,
            comment="Added via GUI",
        )

        self.can_db.messages.append(new_message)
        self.can_db.refresh()

        self.accept()

    def _init_can_message_table(self):
        can_msg_table_layout = QHBoxLayout()

        #### NAME FIELD
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Name"))
        self.name_line_edit = QLineEdit()
        name_layout.addWidget(self.name_line_edit)
        can_msg_table_layout.addLayout(name_layout)

        #### CAN ID
        canid_layout = QVBoxLayout()
        canid_layout.addWidget(QLabel("CAN ID"))
        self.canid_line_edit = QLineEdit(str(self.can_id))
        self.canid_line_edit.setReadOnly(True)
        canid_layout.addWidget(self.canid_line_edit)
        can_msg_table_layout.addLayout(canid_layout)

        #### Type
        type_layout = QVBoxLayout()
        type_layout.addWidget(QLabel("Type"))
        self.type_line_edit = QLineEdit("Extended" if self.is_extended else "Standard")
        self.type_line_edit.setReadOnly(True)
        type_layout.addWidget(self.type_line_edit)
        can_msg_table_layout.addLayout(type_layout)

        #### Length
        length_layout = QVBoxLayout()
        length_layout.addWidget(QLabel("Length"))
        self.length_line_edit = QLineEdit(str(self.data_len))
        self.length_line_edit.setReadOnly(True)
        length_layout.addWidget(self.length_line_edit)
        can_msg_table_layout.addLayout(length_layout)

        self.main_layout.addLayout(can_msg_table_layout)

    def _init_can_signals_table(self):
        can_signals_layout = QVBoxLayout()
        can_signals_layout.addWidget(QLabel("Can Signals:"))

        self.signals_table = QTableWidget(0, len(SIGNAL_HEADERS))
        self.signals_table.setHorizontalHeaderLabels(SIGNAL_HEADERS)
        self.signals_table.verticalHeader().setVisible(False)
        self.signals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        can_signals_layout.addWidget(self.signals_table)

        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Signal")
        add_btn.clicked.connect(self.add_signal_row)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_row)
        btn_layout.addWidget(remove_btn)

        can_signals_layout.addLayout(btn_layout)

        self.main_layout.addLayout(can_signals_layout)

        self.add_signal_row()

    def add_signal_row(self):
        row = self.signals_table.rowCount()
        self.signals_table.insertRow(row)

        for i, col_name in enumerate(SIGNAL_HEADERS):
            if col_name == "Type":
                cell_widget = QComboBox()
                cell_widget.setCurrentIndex(1)
                cell_widget.addItems(TYPE_OPTS)
            elif col_name == "Order":
                cell_widget = QComboBox()
                cell_widget.setCurrentIndex(1)
                cell_widget.addItems(ORDER_OPTS)
            elif col_name in ["Start Bit", "Length"]:
                cell_widget = QLineEdit()
                validator = QIntValidator(0, 64)
                cell_widget.setValidator(validator)
            elif col_name in ["Name", "Unit"]:
                cell_widget = QLineEdit()
            elif col_name == "Value":
                cell_widget = QLineEdit("N/A")
                cell_widget.setReadOnly(True)
            else:
                cell_widget = QLineEdit()
                validator = QDoubleValidator()
                cell_widget.setValidator(validator)
            
            self.signals_table.setCellWidget(row, i, cell_widget)

    def _update_signal_row_val(self, row: int, msg: Message):
        signal_val_col = len(SIGNAL_HEADERS) - 1
        signal_val_widget = self.signals_table.cellWidget(row, signal_val_col)

        try:
            signal = self._get_signal_from_table_row(row, is_test=True)
            message = Message(
                frame_id= self.can_id,
                name="temp",
                length=self.data_len,
                signals=[signal],
                is_extended_frame=False,
            )
        
            decoded = message.decode(msg.data)
            new_val = f"{next(iter(decoded.values())):.3f}"
        except:
            new_val = "N/A"

        signal_val_widget.setText(new_val)

    def on_msgs(self, msgs: list[Message]):
        if not self.recv_msgs:
            return
        
        if not msgs:
            return
        
        for msg in reversed(msgs):
            if msg.arbitration_id != self.can_id:
                continue

            for row in range(self.signals_table.rowCount()):
                self._update_signal_row_val(row, msg)

    def remove_selected_row(self):
        row = self.signals_table.currentRow()
        if row >= 0 and self.signals_table.rowCount() > MIN_SIGNAL_ROWS:
            self.signals_table.removeRow(row)

    def get_signals(self):
        return [
            {
                header: self.signals_table.cellWidget(row, col).text()
                for col, header in enumerate(SIGNAL_HEADERS)
            }
            for row in range(self.signals_table.rowCount())
        ]