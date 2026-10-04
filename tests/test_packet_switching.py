from backend.simulation import run_simulation
from backend.switching.packet_switching import PacketSwitching

def test_packet_switching_has_no_setup():
    assert PacketSwitching.setup_time == 0
    assert run_simulation("packet", 10)["setup_time"] == 0

def test_packet_switching_generates_and_delivers():
    m = run_simulation("packet", 10)
    assert m["packets_generated"] > 0
    assert m["packets_delivered"] > 0
    assert m["throughput"] > 0

def test_higher_offered_traffic_increases_queueing_delay():
    light = run_simulation("packet", 10)
    heavy = run_simulation("packet", 200)
    assert heavy["average_queue_delay"] > light["average_queue_delay"]
