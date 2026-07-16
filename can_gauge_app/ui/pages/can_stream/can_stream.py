from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import Qt

from ui.utils import format_timestamp, format_data, get_data_for_gui

from can import Message
from cantools.database import Database


MONO = "Consolas"

BG = "#1e1e1e"
FG = "#d4d4d4"
TS_COLOR = "#a3d97c"
CHANNEL_COLOR = "#aa9eef" 
ID_COLOR = "#ffd56c"
DLC_COLOR = "#808080"
NAME_COLOR = "#ff6583"
DATA_COLOR = "#d4d4d4"


class CanStream(QtWidgets.QPlainTextEdit):
    def __init__(self, can_db: Database):
        super().__init__()

        self.can_db = can_db

        self.setReadOnly(True)
        self.setMaximumBlockCount(2000)
        self.setUndoRedoEnabled(False)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

        self.setFont(QtGui.QFont(MONO, 19))
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {BG};
                color: {FG};
                border: none;
            }}
        """)
        self.setViewportMargins(5, 5, 5, 5)

        self.recv_msgs = False

    def on_msgs(self, msgs: list[Message]):
        if not self.recv_msgs:
            return

        scroll_bar = self.verticalScrollBar()
        was_at_bottom = scroll_bar.value() >= scroll_bar.maximum() - 4
        
        self.setUpdatesEnabled(False)

        new_rows = []
        for msg in msgs:
            ts, channel, can_id, dlc_str, data = get_data_for_gui(msg)

            try:
                name = self.can_db.get_message_by_frame_id(msg.arbitration_id).name
            except KeyError:
                name = ""

            row = (
                f'<span style="color:{TS_COLOR}">{ts}</span>&nbsp;&nbsp;&nbsp;'
                f'<span style="color:{CHANNEL_COLOR}">{_pad_html(channel, 8)}</span>'
                f'<span style="color:{ID_COLOR}">{can_id:>3}</span>&nbsp;&nbsp;'
                f'<span style="color:{DLC_COLOR}">{_pad_html(dlc_str, 6)}</span>'
                f'<span style="color:{NAME_COLOR}">{_pad_html(name, 24)}</span>'
                f'<span style="color:{DATA_COLOR}">{data}</span>'
            )
            new_rows.append(row)

        self.appendHtml("<br>".join(new_rows))

        if was_at_bottom:
            scroll_bar.setValue(scroll_bar.maximum())

        self.setUpdatesEnabled(True)

def _pad_html(text: str, width: int) -> str:
    """Pad with non-breaking spaces so HTML rendering doesn't collapse it."""
    text = str(text)
    pad = width - len(text)
    if pad > 0:
        text = text + ("&nbsp;" * pad)
    return text