import sys, os, can, cantools

from PyQt5.QtWidgets import QApplication

from decoding.decoder import FrameDecoder
from can_monitor.worker import CANWorker
from demo.demo_worker import DemoCANWoker

from ui.shell import Shell
from ui.pages.can_stream.can_stream import CanStreamPage
from ui.pages.can_stream.raw_can_stream import LogViewer
from ui.pages.gauge import GaugePage

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

def get_msg(msg):

    # 1. Space-separated hex string (e.g., "0a 1b 2c ff")
    hex_spaced = msg.data.hex(' ')

    # 2. Continuous hex string (e.g., "0a1b2cff")
    hex_continuous = msg.data.hex()
    return hex_spaced

def init_workers(worker: CANWorker, decoder: FrameDecoder, gauge_page: GaugePage, can_stream_page: CanStreamPage, log_viewer: LogViewer) -> None:
    worker.cur_message_updated.connect(decoder.on_raw_frame)
    worker.cur_message_updated.connect(lambda msg: log_viewer.append_log_safe(get_msg(msg)))
    decoder.frame_decoded.connect(gauge_page.on_frame)
    decoder.frame_decoded.connect(can_stream_page.on_frame)
    
    worker.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("CanGauge") 
    app.setDesktopFileName("CanGauge")

    shell = Shell()
    gauge_page = GaugePage()
    can_stream_page = CanStreamPage()
    log_viewer = LogViewer()

    shell.add_page("gauge", gauge_page)
    shell.add_page("canstream", can_stream_page)
    shell.add_page("logviewer", log_viewer)
    shell.show_page("gauge")  # always opens here

    if len(sys.argv) == 1:
        worker = init_interface()
    elif len(sys.argv) == 2 and sys.argv[1] == "test":
        worker = DemoCANWoker()
    elif len(sys.argv) == 3 and sys.argv[1] == "test" and int(sys.argv[2]) >= 10:
        worker = DemoCANWoker(int(sys.argv[2]))
    else:
        print("usage: python main.py ['test'] [100]")
        sys.exit(1)
    
    db = cantools.database.Database()
    db.add_dbc_string(open('../subaru_global.dbc').read())
    decoder = FrameDecoder(db)

    init_workers(worker, decoder, gauge_page, can_stream_page, log_viewer)

    shell.showFullScreen()
    # shell.showNormal()
    sys.exit(app.exec_())