from PyQt5.QtCore import QThread, pyqtSignal
import can

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from cantools.database import Database
import time

EMIT_FREQUENCY_HZ = 30

class CANWorker(QThread):
    msg_buffer_emitter = pyqtSignal(list)

    def __init__(self, bus: can.BusABC):
        super().__init__()
        self.bus = bus
        self.running = False

        self.can_msg_buffer = []

    def run(self):
        self.running = True
        
        last_buffer_emit_time = time.monotonic()
        emit_interval = 1.0 / EMIT_FREQUENCY_HZ

        while self.running:
            can_msg = self.bus.recv(timeout=0.1)
            if can_msg is not None:
                self.can_msg_buffer.append(can_msg)

            time_now = time.monotonic()
            if time_now - last_buffer_emit_time >= emit_interval:
                self._emit_buffer()
                last_buffer_emit_time = time_now

    def _emit_buffer(self):
        if self.can_msg_buffer:
            self.msg_buffer_emitter.emit(self.can_msg_buffer)
            self.can_msg_buffer.clear()

    def stop(self):
        self.running = False
        self.wait()