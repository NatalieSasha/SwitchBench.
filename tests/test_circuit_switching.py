from backend.network import PATHS, default_topology
from backend.simulation import run_simulation
from backend.switching.circuit_switching import CircuitSwitching

def test_circuit_setup_and_resource_reservation():
    _, links = default_topology(10_000_000, .01, 20)
    circuit = CircuitSwitching()
    path = circuit.establish(PATHS, links, 10_000_000)
    assert circuit.established and path == tuple(circuit.reserved_links)
    assert all(links[k].reserved_by == "circuit-1" for k in path)
    circuit.release(links)
    assert all(links[k].reserved_by is None for k in path)
    assert run_simulation("circuit", 10)["setup_time"] > 0
