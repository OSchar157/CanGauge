from .requests import (
    engine_speed_req, engine_coolant_temp_req, manifold_pressure_req,
    vehicle_speed_req, throttle_position_req, engine_load_req,
    fuel_level_req, intake_air_temp_req, maf_air_flow_req,
    timing_advance_req, barometric_pressure_req
)
from .decode_resp import (
    decode_engine_speed, decode_engine_coolant_temp, decode_oil_pressure,
    decode_vehicle_speed, decode_throttle_position, decode_engine_load,
    decode_fuel_level, decode_intake_air_temp, decode_maf_air_flow,
    decode_timing_advance, decode_barometric_pressure,
)

PID_REGISTRY = {
    'engine_speed':         {'pid': 0x0C, 'request': engine_speed_req,         'decode': decode_engine_speed,         'unit': 'RPM'},
    'engine_coolant_temp':  {'pid': 0x05, 'request': engine_coolant_temp_req,  'decode': decode_engine_coolant_temp,  'unit': '°C'},
    'manifold_pressure':    {'pid': 0x0B, 'request': manifold_pressure_req,    'decode': decode_oil_pressure,         'unit': 'kPa'},
    'vehicle_speed':        {'pid': 0x0D, 'request': vehicle_speed_req,        'decode': decode_vehicle_speed,        'unit': 'km/h'},
    'throttle_position':    {'pid': 0x11, 'request': throttle_position_req,    'decode': decode_throttle_position,    'unit': '%'},
    'engine_load':          {'pid': 0x04, 'request': engine_load_req,          'decode': decode_engine_load,          'unit': '%'},
    'fuel_level':           {'pid': 0x2F, 'request': fuel_level_req,           'decode': decode_fuel_level,           'unit': '%'},
    'intake_air_temp':      {'pid': 0x0F, 'request': intake_air_temp_req,      'decode': decode_intake_air_temp,      'unit': '°C'},
    'maf_air_flow':         {'pid': 0x10, 'request': maf_air_flow_req,         'decode': decode_maf_air_flow,         'unit': 'g/s'},
    'timing_advance':       {'pid': 0x0E, 'request': timing_advance_req,       'decode': decode_timing_advance,       'unit': '°'},
    'barometric_pressure':  {'pid': 0x33, 'request': barometric_pressure_req,  'decode': decode_barometric_pressure,  'unit': 'kPa'},
}