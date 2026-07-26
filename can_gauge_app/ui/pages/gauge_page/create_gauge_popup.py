import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog,
    QHBoxLayout, QBoxLayout, QScrollArea, QMessageBox
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from ui.gauge_widgets import GAUGE_TYPES

from can import Message
from cantools.database import Database

class CreateGaugePopup(QDialog):
    def __init__(self, parent, can_db: Database, can_id: int, signal_name: str):
        super().__init__(parent)

        self.can_db = can_db
        self.can_id = can_id
        self.signal_name = signal_name

        self.setWindowTitle("Create A Gauge")
        
        master_layout = QVBoxLayout()
        master_layout.addWidget(QLabel(f"Gauge Creation for: {signal_name}"))

        self.gauge_section_layout = QHBoxLayout()
        gauge_config_layout = QVBoxLayout()

        # Gauge selection
        gauge_config_layout.addWidget(QLabel(f"Select gauge type:"))
        self.gauge_sel_dropdown = QComboBox()
        self.gauge_sel_dropdown.addItems(gauge_cls.name for gauge_cls in GAUGE_TYPES.values())
        self.gauge_sel_dropdown.currentTextChanged.connect(self._on_gauge_type_selected)
        gauge_config_layout.addWidget(self.gauge_sel_dropdown)
        
        self.selected_gauge_type = GAUGE_TYPES[self.gauge_sel_dropdown.currentText()]

        # Gauge params
        self.gauge_params_layout = QVBoxLayout()
        self.gauge_params_inputs: dict[str, QLabel] = {}
        self._populate_gauge_params()
        gauge_config_layout.addLayout(self.gauge_params_layout)

        self.gauge_section_layout.addLayout(gauge_config_layout)
        master_layout.addLayout(self.gauge_section_layout)
        
        # Preview window
        self.gauge_preview_widget = None
        self._set_gauge_preview_widget()

        # Add to gauge page button
        add_gauge_btn = QPushButton("Add to Gauge Page")
        add_gauge_btn.clicked.connect(self._on_add_gauge)
        master_layout.addWidget(add_gauge_btn)

        # close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        master_layout.addWidget(close_btn)
        
        self.setLayout(master_layout)

        self.user_created_gauge = None
    
    def _set_gauge_preview_widget(self):
        if self.gauge_preview_widget is not None:
            self.gauge_section_layout.removeWidget(self.gauge_preview_widget)
            self.gauge_preview_widget.deleteLater()

        try:
            args = self.get_gauge_args()
            new_widget = self.selected_gauge_type(**args)
        except:
            new_widget = QLabel("Invalid Arguments!")

        self.gauge_preview_widget = new_widget
        self.gauge_section_layout.addWidget(self.gauge_preview_widget)

    def _on_gauge_type_selected(self, text): 
        self.selected_gauge_type = GAUGE_TYPES[text]
        self.gauge_params_inputs.clear()
        self._populate_gauge_params()
        self._set_gauge_preview_widget()

    def _populate_gauge_params(self):
        self._clear_gauge_params_layout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        gauge_params_layout = QVBoxLayout(content_widget)

        for field in self.selected_gauge_type.get_fields():
            row = QHBoxLayout()
            edit = QLineEdit()

            if field.type == int:
                edit.setValidator(QIntValidator())
            elif field.type == float:
                edit.setValidator(QDoubleValidator())
            
            edit.setText(str(field.default) if field.default is not None else "")
            edit.textChanged.connect(self._set_gauge_preview_widget)

            row.addWidget(QLabel(field.label))
            row.addWidget(edit)

            self.gauge_params_inputs[field.name] = edit

            gauge_params_layout.addLayout(row)
        
        scroll_area.setWidget(content_widget)

        self.gauge_params_layout.addWidget(scroll_area)

    def get_gauge_args(self):
        gauge_args = {
            key: (cast(spec, value_box.text()) if value_box.text() != "" else None)
            for (key, value_box), spec in zip(self.gauge_params_inputs.items(), self.selected_gauge_type.get_fields())
        }

        return gauge_args
    
    def _on_add_gauge(self):
        try:
            args = self.get_gauge_args()
            new_widget = self.selected_gauge_type(**args)
        except:
            QMessageBox.critical(None, "Error", f"Invalid Arguments!")
            return
        
        self.user_created_gauge = (self.selected_gauge_type, args)
        self.accept()

    def _clear_gauge_params_layout(self):
        while self.gauge_params_layout.count():
            item = self.gauge_params_layout.takeAt(0)
            layout = item.layout()
            if layout:
                # clear widgets inside the row layout
                while layout.count():
                    child = layout.takeAt(0) 
                    widget = child.widget()
                    if widget:
                        widget.setParent(None)
                # then delete the row layout itself
                layout.deleteLater()

    def on_msgs(self, msgs: list[Message]):
        if msgs is None:
            return
        
        for msg in reversed(msgs):
            if msg.arbitration_id != self.can_id:
                continue

            signals_dict = self.can_db.decode_message(msg.arbitration_id, msg.data)
            val = signals_dict[self.signal_name]

            try:
                self.gauge_preview_widget.set_value(val)
            except:
                pass

            break


def cast(spec, raw):
    if spec.type != str and raw == "":
        return None
    try:
        return spec.type(raw)
    except (ValueError, TypeError):
        return None