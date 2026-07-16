import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog,
    QHBoxLayout, QBoxLayout, QScrollArea
)
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from ui.gauge_widgets import GAUGE_TYPES

class CreateGaugePopup(QDialog):
    def __init__(self, parent, can_id: int, can_msg_name: str, signal_names: list[str], on_gauge_requested):
        super().__init__(parent)

        self.can_id = can_id
        self.on_gauge_requested = on_gauge_requested

        self.setWindowTitle("Create A Gauge")
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Gauge Creation for: {can_msg_name}"))

        # Signal Select
        layout.addWidget(QLabel(f"Select a singnal:"))
        self.singal_sel_dropdown = QComboBox()
        self.singal_sel_dropdown.addItems(signal_names)
        layout.addWidget(self.singal_sel_dropdown)

        # Gauge selection
        layout.addWidget(QLabel(f"Select gauge type:"))
        self.gauge_sel_dropdown = QComboBox()
        self.gauge_sel_dropdown.addItems(gauge_cls.name for gauge_cls in GAUGE_TYPES.values())
        self.gauge_sel_dropdown.currentTextChanged.connect(self._on_gauge_selected)
        layout.addWidget(self.gauge_sel_dropdown)

        self.selected_gauge_type = GAUGE_TYPES[self.gauge_sel_dropdown.currentText()]

        # Gauge params
        self.gauge_params_layout = QVBoxLayout()
        self.gauge_params_inputs: dict[str, QLabel] = {}
        self._populate_gauge_params()
        layout.addLayout(self.gauge_params_layout)

        # Add to gauge page button
        add_gauge_btn = QPushButton("Add to Gauge Page")
        add_gauge_btn.clicked.connect(self._on_add_gauge)
        layout.addWidget(add_gauge_btn)

        # close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

    def _on_gauge_selected(self, text):
        self.selected_gauge_type = GAUGE_TYPES[text]
        self.gauge_params_inputs.clear()
        self._populate_gauge_params()

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

            row.addWidget(QLabel(field.label))
            row.addWidget(edit)

            self.gauge_params_inputs[field.name] = edit

            gauge_params_layout.addLayout(row)
        
        scroll_area.setWidget(content_widget)

        self.gauge_params_layout.addWidget(scroll_area)

    def _on_add_gauge(self):
        gauge_args = {
            key: cast(spec, value_box.text())
            for (key, value_box), spec in zip(self.gauge_params_inputs.items(), self.selected_gauge_type.get_fields())
        }

        self.on_gauge_requested(self.can_id, self.singal_sel_dropdown.currentText(), self.selected_gauge_type, gauge_args)
        self.close()

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


def cast(spec, raw):
    if spec.type != str and raw == "":
        return None
    try:
        return spec.type(raw)
    except (ValueError, TypeError):
        return None