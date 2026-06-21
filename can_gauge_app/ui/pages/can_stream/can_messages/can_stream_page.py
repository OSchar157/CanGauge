from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
)

from decoding.decoder import DecodedMsg

from .message_rows import ExpandableMessageRow
from .message_rows import MessageRow

from ..styling import (
    ROW_BG, ROW_BG_HOVER, ACCENT, 
    MONO, TEXT_FG, HEADER_FG, BG,
    ROW_BORDER
    )
MAX_ROWS = 500
TRIM_TO = 200 
class CanStreamPage(QWidget):
    """Live CAN stream viewer — header row + scrolling list of clickable frame boxes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(10)

        self.frame_count = 0


        model = QStandardItemModel(0, 6)
        model.setHorizontalHeaderLabels(["Timestamp", "Interface", "ID", "Data Len", "Name", "Data"])

        # ── scrollable row list ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ border: none; background-color: {BG}; }}
            QScrollBar:vertical {{ background: {BG}; width: 10px; }}
            QScrollBar::handle:vertical {{ background: {ROW_BORDER}; border-radius: 5px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.row_container = QWidget()
        self.row_container.setStyleSheet(f"background-color: {BG};")
        self.row_layout = QVBoxLayout(self.row_container)
        self.row_layout.setContentsMargins(0, 0, 0, 0)
        self.row_layout.setSpacing(6)
        self.row_layout.addStretch()  # keeps rows pinned to top as they're inserted

        self.scroll_area.setWidget(self.row_container)
        outer.addWidget(self.scroll_area)

        self._rows = []  # track FrameRow widgets for trimming
        self._ids_seen: dict[int, ExpandableMessageRow | MessageRow] = {} # track which id's we've alraedy made a box for

        # Batch update UI every
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.flush_logs)
        self.timer.start(80)

        self.buffer = []
    
    def flush_logs(self):
        if self.buffer:
            self.row_container.setUpdatesEnabled(False)

            for frame in reversed(self.buffer):
                self.row_layout.insertWidget(0, frame)
            
            self.buffer.clear()

            count = self.row_layout.count()
            if count > MAX_ROWS:
                for _ in range(TRIM_TO):
                    item = self.row_layout.takeAt(self.row_layout.count() - 1)
                    if item is None:
                        break
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()

            self.row_container.setUpdatesEnabled(True)

    def on_msg(self, frame: DecodedMsg):

        if frame.can_id in self._ids_seen: # if we already have a frame for the id
            id_frame = self._ids_seen.get(frame.can_id)
            id_frame._update_data(frame)

        else:
            new_frame = self.create_frame(frame)
            self._ids_seen[frame.can_id] = new_frame

    def create_frame(self, msg: DecodedMsg):
        self.frame_count += 1

        # if len(msg.signals) > 1:
        #     row = ExpandableMessageRow(msg)
        # else:
        #     row = MessageRow(msg)
        row = ExpandableMessageRow(msg)
        self.buffer.append(row)
        
        return row