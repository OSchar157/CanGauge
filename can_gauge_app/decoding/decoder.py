from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal


@dataclass
class DecodedMsg:
    can_id: int
    name: str | None
    timestamp: float
    raw_hex: str
    dlc: int
    channel: str
    signals: dict  # {signal_name: value}


class MsgDecoder(QObject):
    frame_decoded = pyqtSignal(DecodedMsg)

    def __init__(self, db):
        super().__init__()
        self.db = db  # cantools.database.Database — lives here only

    def on_raw_frame(self, msg):
        try:
            msg_def = self.db.get_message_by_frame_id(msg.arbitration_id)
            name = msg_def.name
            signals = self.db.decode_message(msg.arbitration_id, msg.data)
        except Exception:
            name = None
            signals = {}

        decoded = DecodedMsg(
            can_id=msg.arbitration_id,
            name=name,
            timestamp=msg.timestamp,
            raw_hex=" ".join(f"{b:02X}" for b in msg.data),
            dlc=msg.dlc,
            channel=msg.channel,
            signals=signals,
        )
        self.frame_decoded.emit(decoded)