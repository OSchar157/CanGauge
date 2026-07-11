import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QDialog,
    QHBoxLayout, QBoxLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from ui.gauge_widgets import GAUGE_TYPES

class CreateGaugePopup(QDialog):
    def __init__(self, parent, name, signals, on_gauge_requested):
        super().__init__(parent)

        self.on_gauge_requested = on_gauge_requested

        self.setWindowTitle("Create A Gauge")
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Gauge Creation for: {name}"))

        # Signal Select
        layout.addWidget(QLabel(f"Select a singnal:"))
        self.singal_sel_dropdown = QComboBox()
        self.singal_sel_dropdown.addItems(signals.keys())
        layout.addWidget(self.singal_sel_dropdown)
        
        # Function - Not fully implemented yet
        # dropdown_items = ["[" + signal + "]" for signal in signals.keys()]
        # self.function_calc = CalcWidget(dropdown_items)
        # layout.addWidget(self.function_calc)

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
        args = {
            key: cast(spec, value_box.text())
            for (key, value_box), spec in zip(self.gauge_params_inputs.items(), self.selected_gauge_type.get_fields())
        }

        self.on_gauge_requested(self.selected_gauge_type, self.singal_sel_dropdown.currentText(), args)
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

BUTTONS = [
    ["(", ")", "/", "*"],
    ["+", "-", ".", ""],
    ["7", "8", "9", "<-"],
    ["4", "5", "6", ""],
    ["1", "2", "3", "0"],
]


class CalcWidget(QWidget):
    def __init__(self, dropdown_items: list[str]):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Internal token list and cursor
        # Tokens are either plain strings (single chars) or variable strings like "[rpm]"
        self._tokens: list[str] = []
        self._cursor: int = 0  # insertion point between tokens

        layout.addWidget(QLabel("Function"))

        # Display-only box — user cannot click into it
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setFocusPolicy(Qt.NoFocus)
        self.display.setStyleSheet("font-size: 16px; padding: 6px;")
        layout.addWidget(self.display)

        # Cursor nav + signal dropdown row
        nav_row = QHBoxLayout()

        left_btn = QPushButton("◀")
        left_btn.setFixedWidth(60)
        left_btn.clicked.connect(self._move_left)
        nav_row.addWidget(left_btn)

        right_btn = QPushButton("▶")
        right_btn.setFixedWidth(60)
        right_btn.clicked.connect(self._move_right)
        nav_row.addWidget(right_btn)

        nav_row.addWidget(QLabel("Signal:"))
        self.dropdown = QComboBox()
        self.dropdown.addItems(dropdown_items)
        self.dropdown.activated[str].connect(self.on_dropdown)
        nav_row.addWidget(self.dropdown)

        layout.addLayout(nav_row)

        # Numpad grid
        grid = QGridLayout()
        grid.setSpacing(6)
        for row_i, row in enumerate(BUTTONS):
            for col_i, label in enumerate(row):
                if label == "":
                    continue
                btn = QPushButton(label)
                btn.setMinimumHeight(56)  # touch-friendly
                btn.setStyleSheet("font-size: 15px;")
                if label == "<-":
                    btn.clicked.connect(self._delete)
                else:
                    btn.clicked.connect(lambda _, l=label: self._insert_token(l))
                grid.addWidget(btn, row_i, col_i)
        layout.addLayout(grid)

        self._cursor_visible = True
        self._blink_timer = QTimer()
        self._blink_timer.timeout.connect(self._blink)
        self._blink_timer.start(500)  # ms

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_expression(self) -> str:
        """Return the expression as a plain string, variables unwrapped."""
        return "".join(self._tokens)

    def get_display_text(self) -> str:
        """Return what's shown in the display box (with cursor marker)."""
        parts = list(self._tokens)
        parts.insert(self._cursor, "|" if self._cursor_visible else " ")
        return "".join(parts)
    
    def get_expression_vars(self) -> list[str]:
        """Return the variables used in the expression."""
        return [var for var in self._tokens if '[' in var]

    # ------------------------------------------------------------------
    # Internal logic
    # ------------------------------------------------------------------

    def _refresh_display(self):
        self.display.setText(self.get_display_text())

    def _insert_token(self, token: str):
        self._tokens.insert(self._cursor, token)
        self._cursor += 1
        self._refresh_display()

    def _delete(self):
        """Delete the token immediately to the left of the cursor."""
        if self._cursor == 0:
            return
        self._tokens.pop(self._cursor - 1)
        self._cursor -= 1
        self._refresh_display()

    def _move_left(self):
        if self._cursor > 0:
            self._cursor -= 1
            self._refresh_display()

    def _move_right(self):
        if self._cursor < len(self._tokens):
            self._cursor += 1
            self._refresh_display()
    
    def _blink(self):
        self._cursor_visible = not self._cursor_visible
        self._refresh_display()

    def on_dropdown(self, text):
        """Insert a variable token (e.g. '[rpm]') as a single atomic unit."""
        self._insert_token(text)  # text already includes brackets from parent

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CreateGaugePopup(parent=None, id_=123, name=None, signals={"penis": "penis"}, on_gauge_requested=None)
    w.show()
    sys.exit(app.exec_())