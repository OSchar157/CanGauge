import sys
import os
import can
from PyQt5.QtWidgets import QApplication
from can_monitor.worker import CANWorker
from ui.gauge import MainWindow

bitrate = 500000
using_can0 = True
bus_name = f"{'can0' if using_can0 else 'can1'}"

os.system(f'sudo ifconfig {bus_name} down')
os.system(f'sudo ip link set {bus_name} type can bitrate {bitrate}')
os.system(f'sudo ifconfig {bus_name} up')

bus = can.interface.Bus(channel=bus_name, interface='socketcan')
worker = CANWorker(bus)

sys.argv[0] = "CanGauge"
app = QApplication(sys.argv)
app.setApplicationName("CanGauge")
app.setDesktopFileName("CanGauge")
window = MainWindow()

worker.engine_speed_updated.connect(window.rpm_gauge.set_value)
# worker.engine_speed_updated.connect(lambda v: window.engine_speed_text_disp.setText(str(round(v, 1))))

worker.vehicle_speed_updated.connect(lambda kph: window.speedometer.set_value(kph * 0.621371))
# worker.vehicle_speed_updated.connect(lambda kph: window.vehicle_speed_text_disp.setText(str(round(kph * 0.621371, 1))))

worker.start()
window.show()
sys.exit(app.exec_())