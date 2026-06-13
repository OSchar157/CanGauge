import os
import can
import time

from messages import wake_msg, rpm_req
from functions import decode_rmp

bitrate = 500000
using_can0 = True

bus_name = f'{'can0' if using_can0 else 'can1'}'

os.system(f'sudo ip link set {bus_name} type can bitrate {bitrate}')
os.system(f'sudo ifconfig {bus_name} up')

bus = can.interface.Bus(channel= bus_name, interface= 'socketcan')

bus.send(wake_msg)
time.sleep(1)

for _ in range(10):
    bus.send(rpm_req)
    rpm_recv = bus.recv(timeout=2)

    if rpm_recv:
        # print(rpm_recv)
        print(f"rmps: {decode_rmp(rpm_recv)}")
    else:
        print("no response")
        break

    time.sleep(1)


os.system('sudo ifconfig can0 down')