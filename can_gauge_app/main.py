import sys, os, can, cantools

from PyQt5.QtWidgets import QApplication

from decoding.decoder import MsgDecoder
from can_monitor.worker import CANWorker
from demo.demo_worker import DemoCANWoker

from ui.shell import Shell
from ui.pages.gauge import GaugePage
from ui.pages.can_stream.page import CanPage

bitrate = 500000
using_can0 = True
def init_interface() -> CANWorker:
    bus_name = f"{'can0' if using_can0 else 'can1'}"

    os.system(f'sudo ifconfig {bus_name} down')
    os.system(f'sudo ip link set {bus_name} type can bitrate {bitrate}')
    os.system(f'sudo ifconfig {bus_name} up')

    bus = can.interface.Bus(channel=bus_name, interface='socketcan')
    worker = CANWorker(bus)

    return worker

def init_workers(worker: CANWorker, decoder: MsgDecoder, gauge_page: GaugePage, can_page: CanPage) -> None:
    worker.cur_message_updated.connect(decoder.on_raw_frame)
    decoder.frame_decoded.connect(gauge_page.on_msg)
    decoder.frame_decoded.connect(can_page.on_msg)
    
    worker.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("CanGauge") 
    app.setDesktopFileName("CanGauge")

    shell = Shell()
    gauge_page = GaugePage()
    can_page = CanPage()

    shell.add_page("gauge", gauge_page)
    shell.add_page("canpage", can_page)
    # shell.show_page("gauge")  # always opens here
    shell.show_page("canpage")

    if len(sys.argv) == 1:
        worker = init_interface()
    elif len(sys.argv) == 2 and sys.argv[1] == "test":
        worker = DemoCANWoker()
    elif len(sys.argv) == 3 and sys.argv[1] == "test" and int(sys.argv[2]) >= 100:
        worker = DemoCANWoker(int(sys.argv[2]))
    else:
        print("usage: python main.py ['test'] [100]")
        sys.exit(1)
    
    db = cantools.database.Database()
    db.add_dbc_string(open('../subaru_global.dbc').read())
    decoder = MsgDecoder(db)

    init_workers(worker, decoder, gauge_page, can_page)

    # shell.showFullScreen()
    shell.setFixedSize(1080, 648)
    shell.showNormal()
    sys.exit(app.exec_())