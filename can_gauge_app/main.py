import sys, os, can, cantools

from PyQt5.QtWidgets import QApplication

import worker_manager

from ui.shell import Shell
from ui.pages.gauge_page.layout_presets.gauge_layout_preset import GaugeLayoutPreset
from ui.pages.can_table.can_table import CanTable
from ui.pages.can_stream.can_stream import CanStream

import app_state

bitrate = 250000
using_can0 = True

def init_interface():
    bus_name = f"{'can0' if using_can0 else 'can1'}"

    os.system(f'ip link set {bus_name} down')
    os.system(f'ip link set {bus_name} type can bitrate {bitrate}')
    os.system(f'ip link set {bus_name} up')

    bus = can.interface.Bus(channel=bus_name, interface='socketcan')

    return bus

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("CanGauge") 
    app.setDesktopFileName("CanGauge")

    if len(sys.argv) == 1:
        app_state.demo_mode = False
        bus = init_interface()
        worker_manager.init_can(bus)
    elif len(sys.argv) == 2 and sys.argv[1] == "test":
        app_state.demo_mode = True
        worker_manager.init_demo()
    elif len(sys.argv) == 3 and sys.argv[1] == "test" and int(sys.argv[2]) >= 100:
        app_state.demo_mode = True
        worker_manager.init_demo(int(sys.argv[2]))
    else:
        print("usage: python main.py ['test'] [100]")
        sys.exit(1)

    db = cantools.database.Database()
    dbc_path = app_state.dbc_path()
    db.add_dbc_string(open(f'../{dbc_path}').read())
    
    shell = Shell()
    gauge_page = GaugeLayoutPreset(can_db=db)
    can_table = CanTable(on_gauge_requested=gauge_page.add_gauge, can_db=db)
    can_stream = CanStream(can_db=db)

    shell.add_page("gauge", gauge_page)
    shell.add_page("cantable", can_table)
    shell.add_page("canstream", can_stream)
    shell.show_page("gauge")

    shell.showMaximized()
    # shell.setFixedSize(1024, 600)
    # shell.showNormal()
    sys.exit(app.exec_())