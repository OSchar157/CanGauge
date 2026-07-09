from PyQt5.QtCore import QThread, pyqtSignal
import can

from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from cantools.database import Database
import time

@dataclass
class DecodedMsg:
    can_id: int
    name: str | None
    timestamp: float
    raw_hex: str
    dlc: int
    channel: str
    signals: dict

EMIT_FREQUENCY = 30

class CANWorker(QThread):
    decoded_msg_buffer_emitter = pyqtSignal(list)

    def __init__(self, bus: can.BusABC, db: Database):
        super().__init__()
        self.db = db
        self.bus = bus
        self.running = False

        self.decoded_msg_buffer = []

    def run(self):
        self.running = True
        
        last_emit = time.monotonic()
        interval = 1.0 / EMIT_FREQUENCY

        while self.running:
            msg = self.bus.recv(timeout=0.1)
            if msg is not None:
                self._decode_msg(msg)

            now = time.monotonic()
            if now - last_emit >= interval:
                self._emit_buffer()
                last_emit = now

    def _decode_msg(self, msg):
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

        self.decoded_msg_buffer.append(decoded)

    def _emit_buffer(self):
        if self.decoded_msg_buffer:
            self.decoded_msg_buffer_emitter.emit(self.decoded_msg_buffer)
            self.decoded_msg_buffer.clear()

    def stop(self):
        self.running = False
        self.wait()  # wait for thread to finish cleanly