import can
from PyQt5.QtCore import QThread

from can_worker.worker import CANWorker
import time

EMIT_FREQUENCY = 30

class DemoCANWoker(CANWorker):
    def __init__(self, db, speed: int=251):
        super().__init__(db=db, bus=None)
        self.speed = speed
    
    def run(self):
        self.running = True

        last_emit = time.monotonic()
        interval = 1.0 / EMIT_FREQUENCY

        while self.running:
            with can.LogReader("demo/trunced_can_dump.log") as log_file:
                for msg in log_file:

                    if msg is None:
                        continue

                    self._decode_and_buffer(msg)

                    now = time.monotonic()
                    if now - last_emit >= interval:
                        self._emit_buffer()
                        last_emit = now

                    QThread.usleep(self.speed)