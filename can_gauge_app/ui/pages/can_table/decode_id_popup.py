import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog,
    QHBoxLayout, QBoxLayout, QTableWidget, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator

QCOMBOBOX_NO_ARROWS_STYLESHEET = """
    QComboBox::drop-down {
        width: 0px;
        border: none;
    }
"""

MIN_SIGNAL_ROWS = 1

ORDER_OPTS = ["Little Endian", "Big Endian"]
TYPE_OPTS = ["Signed", "Unsigned"]

class DecodeIdPopup(QDialog):
    def __init__(self, can_id, data_len, is_extended, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"Decode CAN ID: {can_id}")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_layout.addWidget(QLabel("Can Message:"))

        self._init_can_message_table(can_id, data_len, is_extended)
        self._init_can_signals_table()

        btn_layout = QVBoxLayout()

        self.save_btn = QPushButton("Save")
        btn_layout.addWidget(self.save_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        self.main_layout.addLayout(btn_layout)

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

        #### Comment
        comment_layout = QVBoxLayout()
        comment_layout.addWidget(QLabel("Comment"))
        self.comment_line_edit = QLineEdit()
        comment_layout.addWidget(self.comment_line_edit)
        can_msg_table_layout.addLayout(comment_layout)

        self.main_layout.addLayout(can_msg_table_layout)

    def _init_can_signals_table(self):
        can_signals_layout = QVBoxLayout()
        can_signals_layout.addWidget(QLabel("Can Signals:"))

        self.signal_headers = [
            "Name", "Type", "Order", "Start Bit", "Length",
            "Scale", "Offset", "Min", "Max", "Unit", "Comment",
        ]

        self.signals_table = QTableWidget(0, len(self.signal_headers))
        self.signals_table.setHorizontalHeaderLabels(self.signal_headers)
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
        for i, col in enumerate(self.signal_headers):
            if col == "Type":
                dropdown = QComboBox()
                dropdown.addItems(TYPE_OPTS)
                dropdown.setStyleSheet(QCOMBOBOX_NO_ARROWS_STYLESHEET)
                self.signals_table.setCellWidget(row, i, dropdown)
            elif col == "Order":
                dropdown = QComboBox()
                dropdown.addItems(ORDER_OPTS)
                dropdown.setStyleSheet(QCOMBOBOX_NO_ARROWS_STYLESHEET)
                self.signals_table.setCellWidget(row, i, dropdown)
            else:
                self.signals_table.setCellWidget(row, i, QLineEdit())

    def remove_selected_row(self):
        row = self.signals_table.currentRow()
        if row >= 0 and self.signals_table.rowCount() > MIN_SIGNAL_ROWS:
            self.signals_table.removeRow(row)

    def get_signals(self):
        return [
            {
                header: self.signals_table.cellWidget(row, col).text()
                for col, header in enumerate(self.signal_headers)
            }
            for row in range(self.signals_table.rowCount())
        ]