import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog,
    QHBoxLayout
)

from PyQt5.QtCore import Qt, pyqtSignal

class CreateGaugePopup(QDialog):
    def __init__(self, parent, id_, name, signals, on_gauge_requested):
        super().__init__(parent)

        self.on_gauge_requested = on_gauge_requested

        self.setWindowTitle("Custom Pop-up")
        self.resize(400, 600)
        
        # Create layout and widgets
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Gauge Creation for: {name or id_}"))

        gauge_params_layout = QVBoxLayout()

        for label, attr in [("Max value", "max_val"), ("Min value", "min_val"), 
                            ("Warn value", "warn_val"), ("Danger value", "danger_val")]:
            row = QHBoxLayout()
            edit = QLineEdit()
            setattr(self, attr, edit)
            row.addWidget(QLabel(label))
            row.addWidget(edit)
            gauge_params_layout.addLayout(row)

        layout.addLayout(gauge_params_layout)


        for w in [self.max_val, self.min_val, self.warn_val, self.danger_val]:
            layout.addWidget(w)

        dropdown_items = ["[" + signal + "]" for signal in signals.keys()]
        self.function_calc = CalcWidget(dropdown_items)
        layout.addWidget(self.function_calc)
        
        add_gauge_btn = QPushButton("Add to Gauge Page")
        add_gauge_btn.clicked.connect(self._on_add_gauge)
        layout.addWidget(add_gauge_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

    def _on_add_gauge(self):
        args = {
            "name": self.function_calc.input.text()[1:-1],
            "min_val": self.min_val.text(),
            "max_val": self.max_val.text(),
            "warn_val": self.warn_val.text(),
            "danger_val": self.danger_val.text()
        }
        self.on_gauge_requested(args)
        self.close()
        

BUTTONS = [
    ["(", ")", "+", "-"],
    ["/", "*", ".", ""],
    ["7", "8", "9", ""],
    ["4", "5", "6", ""],
    ["1", "2", "3", "0"],
]

class CalcWidget(QWidget):
    def __init__(self, dropdown_items):
        super().__init__()
        self.setWindowTitle("Widget")
        layout = QVBoxLayout()
        self.setLayout(layout)

        # layout.addWidget(QLabel("Function"))
        layout.addWidget(QLabel("Signal"))

        # Input box
        self.input = QLineEdit()
        # layout.addWidget(self.input)

        # Dropdown
        self.dropdown = QComboBox()
        self.dropdown.addItems(dropdown_items)
        self.dropdown.activated[str].connect(self.on_dropdown)
        layout.addWidget(self.dropdown)

        # Buttons
        grid = QGridLayout()
        for row_i, row in enumerate(BUTTONS):
            for col_i, label in enumerate(row):
                if label == "":
                    continue
                btn = QPushButton(label)
                btn.clicked.connect(lambda _, l=label: self.input.insert(l))
                grid.addWidget(btn, row_i, col_i)
        # layout.addLayout(grid)

    def on_dropdown(self, text):
        self.input.insert(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CreateGaugePopup()
    w.show()
    sys.exit(app.exec_())