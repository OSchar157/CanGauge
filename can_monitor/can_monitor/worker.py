from PyQt5.QtCore import QThread, pyqtSignal

from .decode_resp import decode_engine_speed, decode_vehicle_speed
from .requests import (
    engine_speed_req, vehicle_speed_req, engine_coolant_temp_req
    )

class CANWorker(QThread):
    engine_speed_updated = pyqtSignal(float)
    vehicle_speed_updated = pyqtSignal(float)

    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.running = False

    def run(self):
        self.running = True
        last_slow_poll = 0

        while self.running:
            # flush stale messages
            while self.bus.recv(timeout=0) is not None:
                pass

            # fast signals — every loop
            self.bus.send(engine_speed_req)
            self.bus.send(vehicle_speed_req)

            # slow signals — every 5 seconds
            # curr_time = time.time()
            # if curr_time - last_slow_poll > 5:
            #     self.bus.send(engine_coolant_temp_req)
            #     last_slow_poll = curr_time
            
            for _ in range(2):
                msg = self.bus.recv(timeout=1.0)
                if msg:
                    if msg.data[2] == 0x0C:  # RPM pid
                        self.engine_speed_updated.emit(decode_engine_speed(msg))
                    elif msg.data[2] == 0x0D:  # speed pid
                        self.vehicle_speed_updated.emit(decode_vehicle_speed(msg))

    def stop(self):
        self.running = False
        self.wait()  # wait for thread to finish cleanly