import can
from PyQt5.QtCore import QThread

from can_worker.worker import CANWorker
import time

EMIT_FREQUENCY = 30

class DemoCANWoker(CANWorker):
    def __init__(self, msg_interval: int=251):
        super().__init__(bus=None)
        self.msg_interval = msg_interval
    
    def run(self):
        self.running = True

        last_buffer_emit_time = time.monotonic()
        interval = 1.0 / EMIT_FREQUENCY

        while self.running:
            with can.LogReader("demo/trunced_can_dump.log") as log_file:
                for can_msg in log_file:

                    if can_msg is None:
                        continue

                    self.can_msg_buffer.append(can_msg)

                    time_now = time.monotonic()
                    if time_now - last_buffer_emit_time >= interval:
                        self._emit_buffer()
                        last_buffer_emit_time = time_now

                    QThread.usleep(self.msg_interval)