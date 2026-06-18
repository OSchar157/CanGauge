import can, os
from .requests import wake_msg, engine_speed_req, vehicle_speed_req, throttle_position_req
from .decode_resp import decode_engine_speed, decode_vehicle_speed, decode_throttle_position, ENGINE_SPEED_RESPONSE_ID, VEHICLE_SPEED_RESPONSE_ID

from .pid_registry import PID_REGISTRY

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
    

def poll_all(bus, pids=None):
    # default to all if none specified
    if pids is None:
        pids = list(PID_REGISTRY.keys())
    
    selected = {k: PID_REGISTRY[k] for k in pids if k in PID_REGISTRY}

    # flush stale messages
    while bus.recv(timeout=0) is not None:
        pass

    # send requests
    for pid in selected.values():
        bus.send(pid['request'])

    # build a response_id -> key lookup for decoding
    response_map = {v['pid']: (k, v['decode']) for k, v in selected.items()}

    # collect responses
    results = {}
    for _ in range(len(selected)):
        msg = bus.recv(timeout=1.0)
        if msg:
            resp_id = msg.data[2]
            if resp_id in response_map:
                key, decode_fn = response_map[resp_id]
                results[key] = decode_fn(msg)

    return results

def poll_three(bus):
    # flush stale messages
    while bus.recv(timeout=0) is not None:
        pass
    # send all requests back to back
    bus.send(engine_speed_req)
    bus.send(vehicle_speed_req)
    bus.send(throttle_position_req)

    # then collect responses
    results = {}
    for _ in range(3):  # expecting 3 responses
        msg = bus.recv(timeout=1.0)
        if msg:
            if msg.data[2] == ENGINE_SPEED_RESPONSE_ID:
                results['rpm'] = decode_engine_speed(msg)
            elif msg.data[2] == VEHICLE_SPEED_RESPONSE_ID:
                results['speed'] = decode_vehicle_speed(msg)
            elif msg.data[2] == ENGINE_SPEED_RESPONSE_ID:
                results['throttle'] = decode_vehicle_speed(msg)
    
    return results