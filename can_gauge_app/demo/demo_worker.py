import can
from PyQt5.QtCore import QThread

from can_monitor.worker import CANWorker

class DemoCANWoker(CANWorker):
    def __init__(self, speed: int=100):
        super().__init__(bus=None)
        self.speed = speed
    
    def run(self):
        self.running = True

        with can.LogReader("demo/can_dump.log") as log_file:
            while self.running:
                for msg in log_file:

                    if msg is None:
                        continue

                    self.cur_message_updated.emit(msg)

                    try:
                        decoded = self.db.decode_message(msg.arbitration_id, msg.data)
                        if 'Engine_RPM' in decoded:
                            self.engine_speed_updated.emit(decoded['Engine_RPM'])
                        if 'FL' in decoded:
                            speed = (decoded['FL'] + decoded['FR'] + decoded['RL'] + decoded['RR']) / 4
                            self.vehicle_speed_updated.emit(speed)
                    except KeyError:
                        pass  # message not in DBC, skip it

                    QThread.msleep(self.speed)