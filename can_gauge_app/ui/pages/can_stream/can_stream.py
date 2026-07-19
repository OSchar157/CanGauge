from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor

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

        self.shell = None
        self.can_db = can_db

        self.setReadOnly(True)
        self.setMaximumBlockCount(2000)
        self.setUndoRedoEnabled(False)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

        self.setFont(QtGui.QFont(MONO, 13))
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {BG};
                color: {FG};
                border: none;
            }}
        """)
        self.setViewportMargins(5, 5, 5, 5)

        self._scratch_doc = QtGui.QTextDocument()
        self._scratch_cursor = QTextCursor(self._scratch_doc)

        # Cache the character format objects so we never recreate them in the loop
        self._fmt_ts = QTextCharFormat()
        self._fmt_ts.setForeground(QColor(TS_COLOR))

        self._fmt_channel = QTextCharFormat()
        self._fmt_channel.setForeground(QColor(CHANNEL_COLOR))

        self._fmt_id = QTextCharFormat()
        self._fmt_id.setForeground(QColor(ID_COLOR))

        self._fmt_dlc = QTextCharFormat()
        self._fmt_dlc.setForeground(QColor(DLC_COLOR))

        self._fmt_name = QTextCharFormat()
        self._fmt_name.setForeground(QColor(NAME_COLOR))

        self._fmt_data = QTextCharFormat()
        self._fmt_data.setForeground(QColor(DATA_COLOR))

    def on_msgs(self, msgs: list[Message]):
        if not msgs:
            return

        scroll_bar = self.verticalScrollBar()
        was_at_bottom = scroll_bar.value() >= scroll_bar.maximum() - 4
        
        self.setUpdatesEnabled(False)

        # 1. Clear the reusable scratchpad document entirely
        self._scratch_doc.clear()
        # Reset cursor position to the start of the cleared document
        self._scratch_cursor.movePosition(QTextCursor.Start)

        get_name = self.can_db.get_message_by_frame_id

        for msg in msgs:
            ts, channel, can_id, dlc_str, data = get_data_for_gui(msg)

            try:
                name = get_name(msg.arbitration_id).name
            except KeyError:
                name = ""

            # Write into the existing, allocated scratchpad memory
            self._scratch_cursor.insertText(f"{ts}   ", self._fmt_ts)
            self._scratch_cursor.insertText(f"{channel:<8}", self._fmt_channel)
            self._scratch_cursor.insertText(f"{can_id:>3}  ", self._fmt_id)
            self._scratch_cursor.insertText(f"{dlc_str:<6}", self._fmt_dlc)
            self._scratch_cursor.insertText(f"{name:<24}", self._fmt_name)
            self._scratch_cursor.insertText(f"{data}\n", self._fmt_data)

        # 2. Drop the compiled fragment into the main visible text box
        ui_cursor = self.textCursor()
        ui_cursor.movePosition(QTextCursor.End)
        ui_cursor.insertFragment(QtGui.QTextDocumentFragment(self._scratch_doc))

        if was_at_bottom:
            scroll_bar.setValue(scroll_bar.maximum())

        self.setUpdatesEnabled(True)
