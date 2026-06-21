import can
from PyQt5.QtCore import QThread

from can_monitor.worker import CANWorker

class DemoCANWoker(CANWorker):
    def __init__(self, speed: int=100):
        super().__init__(bus=None)
        self.speed = speed
    
    def run(self):
        self.running = True

        with can.LogReader("demo/trunced_can_dump.log") as log_file:
            while self.running:
                for msg in log_file:

                    if msg is None:
                        continue

                    self.cur_message_updated.emit(msg)

                    QThread.msleep(self.speed)