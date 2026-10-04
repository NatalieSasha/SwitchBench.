from backend.network import PATHS
from backend.simulation import run_simulation
from backend.switching.virtual_circuit import VirtualCircuit

def test_vc_id_and_path_consistency():
    vc = VirtualCircuit(17)
    path = vc.establish(PATHS)
    assert vc.vc_id == 17
    assert vc.forwarding_table
    assert path == vc.path
    assert run_simulation("virtual_circuit", 10)["setup_time"] > 0

def test_throughput_is_delivered_bits_over_duration():
    metrics = run_simulation("virtual_circuit", 10, simulation_duration=2)
    expected = metrics["packets_delivered"] * 1000 * 8 / 2
    assert metrics["throughput"] == expected
