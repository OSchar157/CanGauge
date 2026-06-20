from PyQt5.QtCore import QThread, pyqtSignal
import cantools, can


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
        self.db = cantools.database.Database()
        self.db.add_dbc_string(open('../subaru_global.dbc').read())

    def run(self):
        self.running = True

        while self.running:
            msg = self.bus.recv(timeout=0.1)

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

    def stop(self):
        self.running = False
        self.wait()  # wait for thread to finish cleanly