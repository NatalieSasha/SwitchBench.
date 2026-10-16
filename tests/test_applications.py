from backend.applications import generate_voice, generate_file, generate_interactive
from backend.application_simulation import run_application_experiment


def test_voice_generator_rate_and_size():
    packets = generate_voice(2, duration=0.061)
    assert len(packets) == 8
    assert all(p.size_bytes == 200 for p in packets)


def test_file_generator_exact_size():
    packets = generate_file(size_mb=0.01, packet_bytes=1500)
    assert sum(p.size_bytes for p in packets) == 10_000
    assert all(0 < p.size_bytes <= 1500 for p in packets)


def test_interactive_generator_pairs_requests_and_responses():
    packets = generate_interactive(2, duration=3, seed=42)
    requests = [p for p in packets if p.app == "interactive_request"]
    responses = [p for p in packets if p.app == "interactive_response"]
    assert len(requests) == len(responses)
    assert all(p.size_bytes == 100 for p in requests)
    assert all(p.size_bytes == 500 for p in responses)


def test_circuit_voice_admission_blocks_over_capacity():
    result = run_application_experiment("voice", 150, "circuit", duration=0.1)
    assert result["call_blocking_probability"] > 0
    assert result["jitter"] == 0
