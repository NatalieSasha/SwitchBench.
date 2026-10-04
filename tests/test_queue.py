from backend.models import Packet
from backend.network import PacketQueue

def test_queue_insert_remove_and_overflow():
    q = PacketQueue(1)
    first = Packet(1, "S", "D", 8, 0, "packet")
    second = Packet(2, "S", "D", 8, 0, "packet")
    assert q.push(first, 0)
    assert not q.push(second, .1)
    assert second.dropped
    assert q.pop(.2) is first
    assert first.queue_exit_time == .2
