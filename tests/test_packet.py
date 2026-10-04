from backend.models import Packet

def test_packet_creation_and_delays():
    p = Packet(1, "S", "D", 8000, 1.0, "packet", 1.1, 1.2, 1.2, 1.3)
    assert p.packet_id == 1
    assert abs(p.queuing_delay - .1) < 1e-9
    assert abs(p.transmission_delay - .1) < 1e-9
    assert abs(p.end_to_end_delay - .3) < 1e-9
