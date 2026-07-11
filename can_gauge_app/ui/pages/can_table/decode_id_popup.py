import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog,
    QHBoxLayout, QBoxLayout, QTableWidget, QHeaderView,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator

from cantools.database import Message, Signal, Database
from cantools.database.conversion import BaseConversion
from cantools.database.can.signal import NamedSignalValue

MIN_SIGNAL_ROWS = 1

ORDER_OPTS = ["Little Endian", "Big Endian"]
TYPE_OPTS = ["Signed", "Unsigned"]

SIGNAL_HEADERS = [
            "Name", "Type", "Order", "Start Bit", "Length",
            "Scale", "Offset", "Min", "Max", "Unit",
            ]

class DecodeIdPopup(QDialog):
    def __init__(self, can_id, data_len, is_extended, db: Database, parent=None):
        super().__init__(parent)
        self.can_id = can_id
        self.data_len = data_len
        self.db = db

        self.setWindowTitle(f"Decode CAN ID: {can_id}")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.addWidget(QLabel("Can Message:"))

        self._init_can_message_table(can_id, data_len, is_extended)
        self._init_can_signals_table()

        btn_layout = QVBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._on_click_save_btn)
        btn_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        self.main_layout.addLayout(btn_layout)

    def _on_click_save_btn(self):
        new_signals = []
        for row in range(self.signals_table.rowCount()):
            for col in range(self.signals_table.columnCount()):
                widget = self.signals_table.cellWidget(row, col)

                if isinstance(widget, QComboBox):
                    text = widget.currentText()
                elif isinstance(widget, QLineEdit):
                    text = widget.text()
                
                col_header = self.signals_table.horizontalHeaderItem(col).text()

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
                    scale = float(text)
                elif col_header == "Offset":
                    offset = float(text)
                elif col_header == "Min":
                    minimum = float(text)
                elif col_header == "Max":
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
            new_signals.append(signal)

        new_message = Message(
            frame_id= int(self.can_id.strip(), 16),
            name=self.name_line_edit.text(),
            length=int(self.data_len),
            signals=new_signals,
            is_extended_frame=False,
            comment="Added via GUI",
        )

        print(new_message, new_signals)

        self.db.messages.append(new_message)
        self.db.refresh()

        self.accept()

    def _init_can_message_table(self, can_id, data_len, is_extended):
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
        self.canid_line_edit = QLineEdit(can_id)
        self.canid_line_edit.setReadOnly(True)
        canid_layout.addWidget(self.canid_line_edit)
        can_msg_table_layout.addLayout(canid_layout)

        #### Type
        type_layout = QVBoxLayout()
        type_layout.addWidget(QLabel("Type"))
        self.type_line_edit = QLineEdit("Extended" if is_extended else "Standard")
        self.type_line_edit.setReadOnly(True)
        type_layout.addWidget(self.type_line_edit)
        can_msg_table_layout.addLayout(type_layout)

        #### Length
        length_layout = QVBoxLayout()
        length_layout.addWidget(QLabel("Length"))
        self.length_line_edit = QLineEdit(data_len)
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

        for i, col in enumerate(SIGNAL_HEADERS):
            if col == "Type":
                cell_widget = QComboBox()
                cell_widget.setCurrentIndex(1)
                cell_widget.addItems(TYPE_OPTS)
            elif col == "Order":
                cell_widget = QComboBox()
                cell_widget.setCurrentIndex(1)
                cell_widget.addItems(ORDER_OPTS)
            elif col in ["Start Bit", "Length"]:
                cell_widget = QLineEdit()
                validator = QIntValidator(0, 64)
                cell_widget.setValidator(validator)
            elif col in ["Name", "Unit"]:
                cell_widget = QLineEdit()
            else:
                cell_widget = QLineEdit()
                validator = QDoubleValidator()
                cell_widget.setValidator(validator)
            
            self.signals_table.setCellWidget(row, i, cell_widget)

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