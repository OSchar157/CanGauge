from PyQt5.QtCore import QThread, pyqtSignal
import time
from .decode_resp import decode_engine_speed, decode_vehicle_speed
from .pid_registry import PID_REGISTRY
from .poll_reqs import poll_all


class CANWorker(QThread):
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


    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.running = False

    def run(self):
        self.running = True

        while self.running:
            results = poll_all(self.bus, ['engine_speed', 'vehicle_speed'])

            for key, value in results.items():
                if key == 'engine_speed':
                    self.engine_speed_updated.emit(value)
                elif key == 'vehicle_speed':
                    self.vehicle_speed_updated.emit(value)
                elif key == 'manifold_pressure':
                    self.manifold_pressure_updated.emit(value)
                elif key == 'throttle_position':
                    self.throttle_position_updated.emit(value)
                elif key == 'engine_load':
                    self.engine_load_updated.emit(value)
                elif key == 'fuel_level':
                    self.fuel_level_updated.emit(value)
                elif key == 'intake_air_temp':
                    self.intake_air_temp_updated.emit(value)
                elif key == 'maf_air_flow':
                    self.maf_air_flow_updated.emit(value)
                elif key == 'timing_advance':
                    self.timing_advance_updated.emit(value)
                elif key == 'barometric_pressure':
                    self.barometric_pressure_updated.emit(value)

    def stop(self):
        self.running = False
        self.wait()  # wait for thread to finish cleanly