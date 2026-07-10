from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import Qt
import time


from can_worker.worker import DecodedMsg

MONO = "Consolas"  # or "JetBrains Mono", "Cascadia Code", whatever you've got

BG = "#1e1e1e"
FG = "#d4d4d4"
TS_COLOR = "#a3d97c"
CHANNEL_COLOR = "#aa9eef" 
ID_COLOR = "#ffd56c"
DLC_COLOR = "#808080"
NAME_COLOR = "#ff6583"
DATA_COLOR = "#d4d4d4"


class CanStream(QtWidgets.QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumBlockCount(2000)
        self.setUndoRedoEnabled(False)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

        self.setFont(QtGui.QFont("Courier New", 19))
        # self.setFont(_pick_mono_font(10))
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {BG};
                color: {FG};
                border: none;
            }}
        """)
        self.setViewportMargins(5, 5, 5, 5)

    def on_msgs(self, msgs: list[DecodedMsg]):

        scroll_bar = self.verticalScrollBar()
        was_at_bottom = scroll_bar.value() >= scroll_bar.maximum() - 4
        
        self.setUpdatesEnabled(False)

        lines = []
        for msg in msgs:
            ts = time.strftime("%H:%M:%S", time.localtime(msg.timestamp)) + f".{int(msg.timestamp % 1 * 1000):03d}"
            channel = msg.channel
            can_id = f"{msg.can_id:03X}"
            dlc_str = f"[{msg.data_len}]"
            name = (msg.name or "").replace("_", " ")
            data = msg.raw_hex

            line = (
                f'<span style="color:{TS_COLOR}">{ts}</span>&nbsp;&nbsp;&nbsp;'
                f'<span style="color:{CHANNEL_COLOR}">{_pad_html(channel, 8)}</span>'
                f'<span style="color:{ID_COLOR}">{can_id:>3}</span>&nbsp;&nbsp;'
                f'<span style="color:{DLC_COLOR}">{_pad_html(dlc_str, 6)}</span>'
                f'<span style="color:{NAME_COLOR}">{_pad_html(name, 24)}</span>'
                f'<span style="color:{DATA_COLOR}">{data}</span>'
            )
            lines.append(line)

        self.appendHtml("<br>".join(lines))

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

def _pick_mono_font(point_size: int=10) -> QtGui.QFont:
    candidates = ["JetBrains Mono", "Cascadia Mono", "Consolas", "DejaVu Sans Mono", "Courier New"]
    families = set(QtGui.QFontDatabase().families())
    for name in candidates:
        if name in families:
            print(name)
            return QtGui.QFont(name, point_size)
    # last resort: ask Qt for *any* monospace font on the system
    font = QtGui.QFont()
    font.setStyleHint(QtGui.QFont.Monospace)
    font.setPointSize(point_size)
    return font
