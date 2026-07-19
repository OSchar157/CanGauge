demo_mode = False
demo_dbc_path = "subaru_global_TESTING.dbc"
normal_dbc_path = "Orion_CANBUS.dbc"

def dbc_path():
    return demo_dbc_path if demo_mode else normal_dbc_path