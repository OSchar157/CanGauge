import can


def decode_rpm(msg: can.Message) -> float:
    """PID 0x0C — Engine RPM (resolution: 0.25 RPM)"""
    if not (
        len(msg.data) >= 5 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x0C
    ):
        return -1

    A = msg.data[3]
    B = msg.data[4]

    return ((256 * A) + B) / 4


def decode_engine_coolant_temp(msg: can.Message) -> float:
    """PID 0x05 — Engine Coolant Temperature in °C (range: -40 to 215°C)"""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x05
    ):
        return -1

    A = msg.data[3]

    return A - 40


def decode_oil_pressure(msg: can.Message) -> float:
    """PID 0x0D — Note: OBD-II has no standard oil pressure PID.
    This decodes intake manifold pressure (MAP) in kPa instead,
    which is the closest standard analog. Range: 0-255 kPa."""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x0B
    ):
        return -1

    A = msg.data[3]

    return float(A)  # kPa, 1:1 scaling


def decode_vehicle_speed(msg: can.Message) -> float:
    """PID 0x0D — Vehicle Speed in km/h (range: 0-255 km/h)"""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x0D
    ):
        return -1

    A = msg.data[3]

    return float(A)


def decode_throttle_position(msg: can.Message) -> float:
    """PID 0x11 — Throttle Position as % (range: 0-100%)"""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x11
    ):
        return -1

    A = msg.data[3]

    return (A / 255) * 100


def decode_engine_load(msg: can.Message) -> float:
    """PID 0x04 — Calculated Engine Load as % (range: 0-100%)"""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x04
    ):
        return -1

    A = msg.data[3]

    return (A / 255) * 100


def decode_fuel_level(msg: can.Message) -> float:
    """PID 0x2F — Fuel Tank Level as % (range: 0-100%)"""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x2F
    ):
        return -1

    A = msg.data[3]

    return (A / 255) * 100


def decode_intake_air_temp(msg: can.Message) -> float:
    """PID 0x0F — Intake Air Temperature in °C (range: -40 to 215°C)"""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x0F
    ):
        return -1

    A = msg.data[3]

    return A - 40


def decode_maf_air_flow(msg: can.Message) -> float:
    """PID 0x10 — MAF Air Flow Rate in g/s (range: 0-655.35 g/s)"""
    if not (
        len(msg.data) >= 5 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x10
    ):
        return -1

    A = msg.data[3]
    B = msg.data[4]

    return ((256 * A) + B) / 100


def decode_timing_advance(msg: can.Message) -> float:
    """PID 0x0E — Timing Advance in degrees before TDC (range: -64 to 63.5°)"""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x0E
    ):
        return -1

    A = msg.data[3]

    return (A / 2) - 64


def decode_o2_sensor_voltage(msg: can.Message, sensor_pid: int = 0x14) -> float:
    """PIDs 0x14-0x1B — O2 Sensor Voltage in V (range: 0-1.275V).
    Pass sensor_pid for the specific sensor (0x14=Bank1/S1 ... 0x1B=Bank2/S4)."""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == sensor_pid and
        0x14 <= sensor_pid <= 0x1B
    ):
        return -1

    A = msg.data[3]

    return A / 200


def decode_barometric_pressure(msg: can.Message) -> float:
    """PID 0x33 — Barometric Pressure in kPa (range: 0-255 kPa)"""
    if not (
        len(msg.data) >= 4 and
        msg.data[1] == 0x41 and
        msg.data[2] == 0x33
    ):
        return -1

    A = msg.data[3]

    return float(A)