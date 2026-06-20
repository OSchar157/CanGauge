import sys, os, can

from PyQt5.QtWidgets import QApplication

from can_monitor.worker import CANWorker
from demo.demo_worker import DemoCANWoker

from ui.shell import Shell
from ui.pages.gauge import GaugePage
from ui.pages.can_stream_test import CanStreamPage

bitrate = 500000
using_can0 = True
def init_can() -> CANWorker:
    bus_name = f"{'can0' if using_can0 else 'can1'}"

    os.system(f'sudo ifconfig {bus_name} down')
    os.system(f'sudo ip link set {bus_name} type can bitrate {bitrate}')
    os.system(f'sudo ifconfig {bus_name} up')

    bus = can.interface.Bus(channel=bus_name, interface='socketcan')
    worker = CANWorker(bus)

    return worker

def init_workers(worker: CANWorker, gauge_page: GaugePage, can_stream_page: CanStreamPage) -> None:
    worker.engine_speed_updated.connect(gauge_page.rpm_gauge.set_value)
    worker.vehicle_speed_updated.connect(lambda kph: gauge_page.speedometer.set_value(kph * 0.621371))

    worker.cur_message_updated.connect(can_stream_page.add_frame)

    worker.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("CanGauge") 
    app.setDesktopFileName("CanGauge")

    shell = Shell()
    gauge_page = GaugePage()
    can_stream_page = CanStreamPage()

    shell.add_page("gauge", gauge_page)
    shell.add_page("canstream", can_stream_page)
    shell.show_page("gauge")  # always opens here

    if len(sys.argv) == 1:
        worker = init_can()
    elif len(sys.argv) == 2 and sys.argv[1] == "test":
        worker = DemoCANWoker()
    else:
        print("usage: python main.py ['test']")
        sys.exit(1)
    
    init_workers(worker, gauge_page, can_stream_page)

    shell.showFullScreen()
    sys.exit(app.exec_())