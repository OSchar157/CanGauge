import sys, os, can, cantools

from PyQt5.QtWidgets import QApplication

from can_worker.worker import CANWorker
from demo.demo_worker import DemoCANWoker

from ui.shell import Shell
from ui.pages.gauge_page.gauge_page import GaugePage
from ui.pages.can_table.can_table import CanTable
from ui.pages.can_stream.can_stream import CanStream

bitrate = 500000
using_can0 = True

def init_interface(db) -> CANWorker:
    bus_name = f"{'can0' if using_can0 else 'can1'}"
    print(id(db))

    os.system(f'sudo ifconfig {bus_name} down')
    os.system(f'sudo ip link set {bus_name} type can bitrate {bitrate}')
    os.system(f'sudo ifconfig {bus_name} up')

    bus = can.interface.Bus(channel=bus_name, interface='socketcan')
    worker = CANWorker(bus, db)

    return worker

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("CanGauge") 
    app.setDesktopFileName("CanGauge")

    db = cantools.database.Database()
    db.add_dbc_string(open('../subaru_global_TESTING.dbc').read())
    
    shell = Shell()
    gauge_page = GaugePage()
    can_table = CanTable(on_gauge_requested=gauge_page.add_gauge, db=db)
    can_stream = CanStream()

    shell.add_page("gauge", gauge_page)
    shell.add_page("cantable", can_table)
    shell.add_page("canstream", can_stream)
    shell.show_page("cantable")


    if len(sys.argv) == 1:
        worker = init_interface(db)
    elif len(sys.argv) == 2 and sys.argv[1] == "test":
        worker = DemoCANWoker(db)
    elif len(sys.argv) == 3 and sys.argv[1] == "test" and int(sys.argv[2]) >= 100:
        worker = DemoCANWoker(db, int(sys.argv[2]))
    else:
        print("usage: python main.py ['test'] [100]")
        sys.exit(1)
    
    worker.decoded_msg_buffer_emitter.connect(gauge_page.on_msgs)
    worker.decoded_msg_buffer_emitter.connect(can_table.on_msgs)
    worker.decoded_msg_buffer_emitter.connect(can_stream.on_msgs)
    
    worker.start()

    shell.showMaximized()
    # shell.setFixedSize(1024, 600)
    # shell.showNormal()
    sys.exit(app.exec_())