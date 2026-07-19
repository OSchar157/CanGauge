import time
from can import Message

def format_timestamp(timestamp: float):
    return time.strftime("%H:%M:%S", time.localtime(timestamp or time.time())) + f".{int((timestamp or 0) % 1 * 1000):03d}"

def format_data(data: bytearray):
    return " ".join(f"{byte:02X}" for byte in data)

def dec_to_hex(hex: str):
    return f"{hex:02X}"

def get_data_for_gui(msg: Message):
    ts = format_timestamp(msg.timestamp)
    channel = str(msg.channel)
    can_id = dec_to_hex(msg.arbitration_id)
    dlc_str = f"[{msg.dlc}]"
    data = format_data(msg.data)

    return ts, channel, can_id, dlc_str, data