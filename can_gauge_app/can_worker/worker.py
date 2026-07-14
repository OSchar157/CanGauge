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
    data_len: int
    channel: str
    signals: dict
    is_extended: bool
    raw_frame: can.Message

EMIT_FREQUENCY_HZ = 30

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
        
        last_buffer_emit = time.monotonic()
        emit_interval = 1.0 / EMIT_FREQUENCY_HZ

        while self.running:
            can_msg = self.bus.recv(timeout=0.1)
            if can_msg is not None:
                self._decode_and_buffer(can_msg)

            now = time.monotonic()
            if now - last_buffer_emit >= emit_interval:
                self._emit_buffer()
                last_buffer_emit = now

    def _decode_and_buffer(self, msg:can.Message):
        try:
            dbc_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
            name = dbc_msg.name
            signals = self.db.decode_message(msg.arbitration_id, msg.data)
        except:
            name = None
            signals = {}

        decoded = DecodedMsg(
            can_id=msg.arbitration_id,
            name=name,
            timestamp=msg.timestamp,
            raw_hex=" ".join(f"{byte:02X}" for byte in msg.data),
            data_len=msg.dlc,
            channel=msg.channel,
            signals=signals,
            is_extended=msg.is_extended_id,
            raw_frame = msg
        )

        self.decoded_msg_buffer.append(decoded)

    def _emit_buffer(self):
        if self.decoded_msg_buffer:
            self.decoded_msg_buffer_emitter.emit(self.decoded_msg_buffer)
            self.decoded_msg_buffer.clear()

    def stop(self):
        self.running = False
        self.wait()  # wait for thread to finish cleanly