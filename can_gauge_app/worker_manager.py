from can_worker.worker import CANWorker
from demo.demo_worker import DemoCANWoker
worker = None
current_owner = None
current_slot = None

def init_can(bus):
    global worker
    worker = CANWorker(bus)
    worker.start()

def init_demo(msg_interval):
    global worker
    worker = DemoCANWoker(msg_interval)
    worker.start()

def set_owner(owner, slot):
    global current_owner, current_slot

    if owner is current_owner:
        return

    if current_slot is not None:
        worker.msg_buffer_emitter.disconnect(current_slot)

    current_owner = owner
    current_slot = slot
    worker.msg_buffer_emitter.connect(slot)