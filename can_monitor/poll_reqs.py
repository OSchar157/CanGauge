import can, os
from .requests import wake_msg, rpm_req
from .decode_resp import decode_rpm

def init_reqsts():
    bitrate = 500000
    using_can0 = True

    bus_name = f'{'can0' if using_can0 else 'can1'}'

    os.system(f'sudo ifconfig {bus_name} down')
    os.system(f'sudo ip link set {bus_name} type can bitrate {bitrate}')
    os.system(f'sudo ifconfig {bus_name} up')

    bus = can.interface.Bus(channel= bus_name, interface= 'socketcan')
    bus.send(wake_msg)

    return bus


def poll_rpm(bus: can.BusABC) -> float:
    # flush stale messages
    while bus.recv(timeout=0) is not None:
        pass
    
    # send request and wait for fresh response
    bus.send(rpm_req)
    rpm_recv = bus.recv(timeout=1.0)  # wait up to 1 second
    
    if rpm_recv:
        return decode_rpm(rpm_recv)
    return -1
    