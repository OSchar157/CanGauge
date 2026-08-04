import sys, os, can, cantools

from PyQt5.QtWidgets import QApplication

import worker_manager

from ui.shell import Shell

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
    app.setStyle("Fusion")

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
    
    shell = Shell(can_db=db)

    shell.showFullScreen()
    # shell.showMaximized()
    # shell.setFixedSize(1024, 600)
    # shell.showNormal()
    sys.exit(app.exec_())