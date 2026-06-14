import can, os
from .requests import wake_msg, engine_speed_req, vehicle_speed_req
from .decode_resp import decode_engine_speed, decode_vehicle_speed, ENGINE_SPEED_RESPONSE_ID, VEHICLE_SPEED_RESPONSE_ID

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
    bus.send(engine_speed_req)
    rpm_recv = bus.recv(timeout=1.0)  # wait up to 1 second
    
    if rpm_recv:
        return decode_engine_speed(rpm_recv)
    return -1
    
def poll_all(bus):
    # flush stale messages
    while bus.recv(timeout=0) is not None:
        pass
    # send all requests back to back
    bus.send(engine_speed_req)
    bus.send(vehicle_speed_req)

    # then collect responses
    results = {}
    for _ in range(2):  # expecting 2 responses
        msg = bus.recv(timeout=1.0)
        if msg:
            if msg.data[2] == ENGINE_SPEED_RESPONSE_ID:
                results['rpm'] = decode_engine_speed(msg)
            elif msg.data[2] == VEHICLE_SPEED_RESPONSE_ID:
                results['speed'] = decode_vehicle_speed(msg)
    
    return results