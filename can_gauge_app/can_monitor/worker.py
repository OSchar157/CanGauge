from PyQt5.QtCore import QThread, pyqtSignal
import can


class CANWorker(QThread):
    cur_message_updated = pyqtSignal(can.Message) #for every incoming message

    engine_speed_updated = pyqtSignal(float)
    vehicle_speed_updated = pyqtSignal(float)
    manifold_pressure_updated = pyqtSignal(float)
    throttle_position_updated = pyqtSignal(float)
    engine_load_updated = pyqtSignal(float)
    fuel_level_updated = pyqtSignal(float)
    intake_air_temp_updated = pyqtSignal(float)
    maf_air_flow_updated = pyqtSignal(float)
    timing_advance_updated = pyqtSignal(float)
    barometric_pressure_updated = pyqtSignal(float)


    def __init__(self, bus: can.BusABC):
        super().__init__()
        self.bus = bus
        self.running = False

    def run(self):
        self.running = True

        while self.running:
            msg = self.bus.recv(timeout=0.1)

            if msg is None:
                continue

            self.cur_message_updated.emit(msg)

    def stop(self):
        self.running = False
        self.wait()  # wait for thread to finish cleanly