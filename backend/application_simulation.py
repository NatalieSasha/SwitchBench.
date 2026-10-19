"""Simplified application-level experiments for the SwitchBench teaching simulator.

This is an application-oriented model, not a full TCP/IP or discrete-event network stack.
It uses link serialization clocks, propagation delay, bounded waiting estimates, and
explicit circuit admission for voice calls. Keep assumptions visible in any report.
"""
from __future__ import annotations
from collections import defaultdict
from statistics import mean
from .applications import generate_voice, generate_file, generate_interactive
from .network import PATHS, default_topology

SWITCH_TYPES = ("packet", "circuit", "virtual_circuit")


def _percentile(values, pct):
    if not values:
        return 0.0
    values = sorted(values)
    index = max(0, min(len(values) - 1, int(__import__("math").ceil(pct * len(values)) - 1)))
    return float(values[index])


def _run_shared_packets(packets, switching_type, bandwidth, queue_capacity, propagation_delay, setup_time):
    """Forward packets in arrival order, using shared FIFO link availability clocks."""
    _, links = default_topology(bandwidth, propagation_delay, queue_capacity)
    delivered = []
    for packet_id, packet in enumerate(sorted(packets, key=lambda p: (p.time, p.flow_id, p.index, p.app))):
        if packet.time < setup_time:
            ready = setup_time
        else:
            ready = packet.time
        path = PATHS[packet_id % len(PATHS)] if switching_type == "packet" else PATHS[0]
        now, queued = ready, False
        for link_name in path:
            link = links[link_name]
            tx = packet.size_bytes * 8 / link.bandwidth
            start = max(now, link.busy_until)
            # Approximate bounded FIFO occupancy from the waiting time at this link.
            if start > now and tx > 0 and (start - now) / tx >= queue_capacity:
                queued = True
                break
            link.busy_time += tx
            link.busy_until = start + tx
            now = start + tx + link.propagation_delay
        if not queued:
            delivered.append((packet, now))
    return delivered


def run_application_experiment(application, load, switching_type, bandwidth=10_000_000,
                               queue_capacity=20, duration=5.0, propagation_delay=0.01,
                               file_size_mb=5.0):
    """Run one app/load/model case and return comparable metrics.

    load = concurrent calls for voice, competing users for interactive, or background
    voice calls for file transfer. File experiments include a single file transfer.
    """
    if application not in ("voice", "file", "interactive"):
        raise ValueError("application must be voice, file, or interactive")
    if switching_type not in SWITCH_TYPES:
        raise ValueError(f"switching_type must be one of {', '.join(SWITCH_TYPES)}")
    if load < 0 or (application != "file" and load < 1) or bandwidth <= 0 or queue_capacity < 1 or duration <= 0:
        raise ValueError("load must be non-negative (positive for voice/interactive); bandwidth, queue capacity, and duration must be positive")

    if application == "voice":
        packets = generate_voice(load, duration)
        offered_calls = load
        setup_time = 2 * propagation_delay if switching_type != "packet" else 0.0
    elif application == "file":
        packets = generate_file(file_size_mb)
        # Background voice traffic is present in packet/VC models. For circuit, the file
        # owns a dedicated circuit after setup; the simplified model does not multiplex
        # separate circuit reservations with this background stream.
        if switching_type != "circuit":
            packets += generate_voice(load, duration)
        offered_calls = load
        setup_time = 2 * propagation_delay if switching_type != "packet" else 0.0
    else:
        packets = generate_interactive(load, duration)
        offered_calls = load
        setup_time = 2 * propagation_delay if switching_type != "packet" else 0.0

    if application == "voice" and switching_type == "circuit":
        # Admission control: 80 kb/s per call, with a dedicated 3-hop circuit.
        capacity_calls = int(bandwidth // 80_000)
        admitted = min(load, capacity_calls)
        rejected = load - admitted
        admitted_packets = [p for p in packets if int(p.flow_id.split("-")[1]) < admitted]
        # No queue contention for admitted circuits; fixed service slice per call.
        delay = 3 * propagation_delay + (200 * 8 / 80_000)
        delays = [delay for _ in admitted_packets]
        return {
            "application": application, "load": load, "switching_type": switching_type,
            "packets_generated": len(packets), "packets_delivered": len(admitted_packets),
            "packets_lost": len(packets) - len(admitted_packets),
            "packet_delivery_ratio": len(admitted_packets) / len(packets) if packets else 0.0,
            "average_end_to_end_delay": mean(delays) if delays else 0.0,
            "p95_end_to_end_delay": _percentile(delays, .95),
            "jitter": 0.0, "out_of_order_count": 0,
            "call_blocking_probability": rejected / load if load else 0.0,
            "file_completion_time": 0.0, "goodput_bps": len(admitted_packets) * 200 * 8 / duration,
            "average_response_time": 0.0, "p95_response_time": 0.0,
            "setup_time": setup_time, "reserved_bandwidth_bps": admitted * 80_000,
        }

    if application == "file" and switching_type == "circuit":
        # A dedicated circuit serializes the file continuously without a packet queue.
        file_packets = [p for p in packets if p.flow_id == "file-0"]
        tx = sum(p.size_bytes * 8 for p in file_packets) / bandwidth
        completion = setup_time + tx + 3 * propagation_delay
        delays = [setup_time + (p.index + 1) * (1500 * 8 / bandwidth) + 3 * propagation_delay
                  for p in file_packets]
        # The final packet may be smaller than 1500 bytes; completion uses exact total bytes.
        total_bits = sum(p.size_bytes * 8 for p in file_packets)
        return {
            "application": application, "load": load, "switching_type": switching_type,
            "packets_generated": len(file_packets), "packets_delivered": len(file_packets),
            "packets_lost": 0, "packet_delivery_ratio": 1.0,
            "average_end_to_end_delay": mean(delays) if delays else 0.0,
            "p95_end_to_end_delay": _percentile(delays, .95),
            "jitter": 0.0, "out_of_order_count": 0, "call_blocking_probability": 0.0,
            "file_completion_time": completion, "goodput_bps": total_bits / completion if completion > 0 else 0.0,
            "average_response_time": 0.0, "p95_response_time": 0.0,
            "setup_time": setup_time, "reserved_bandwidth_bps": bandwidth,
        }

    delivered = _run_shared_packets(packets, switching_type, bandwidth, queue_capacity,
                                    propagation_delay, setup_time)
    delays = [arrival - packet.time for packet, arrival in delivered]
    per_flow = defaultdict(list)
    for packet, arrival in delivered:
        per_flow[packet.flow_id].append((packet.index, packet.app, packet.time, arrival, packet.size_bytes))
    jitter_samples = []
    for flow_items in per_flow.values():
        ordered = sorted(flow_items, key=lambda x: (x[0], x[1]))
        flow_delays = [x[3] - x[2] for x in ordered]
        jitter_samples.extend(abs(flow_delays[i] - flow_delays[i-1]) for i in range(1, len(flow_delays)))
    response_times = []
    if application == "interactive":
        requests = {}
        for packet, arrival in delivered:
            if packet.app == "interactive_request":
                requests[(packet.flow_id, packet.index)] = arrival
            elif packet.app == "interactive_response" and (packet.flow_id, packet.index) in requests:
                response_times.append(arrival - requests[(packet.flow_id, packet.index)])
    file_packets = [(p, a) for p, a in delivered if p.flow_id == "file-0"]
    file_completion = max((a for _, a in file_packets), default=0.0) - min((p.time for p, _ in file_packets), default=0.0)
    generated = len(packets)
    delivered_count = len(delivered)
    total_delivered_bits = sum(p.size_bytes * 8 for p, _ in delivered)
    return {
        "application": application, "load": load, "switching_type": switching_type,
        "packets_generated": generated, "packets_delivered": delivered_count,
        "packets_lost": generated - delivered_count,
        "packet_delivery_ratio": delivered_count / generated if generated else 0.0,
        "average_end_to_end_delay": mean(delays) if delays else 0.0,
        "p95_end_to_end_delay": _percentile(delays, .95),
        "jitter": mean(jitter_samples) if jitter_samples else 0.0,
        "out_of_order_count": 0,  # this model schedules packets in offered order; no reordering claim is made
        "call_blocking_probability": 0.0,
        "file_completion_time": file_completion if application == "file" else 0.0,
        "goodput_bps": total_delivered_bits / duration,
        "average_response_time": mean(response_times) if response_times else 0.0,
        "p95_response_time": _percentile(response_times, .95),
        "setup_time": setup_time,
        "reserved_bandwidth_bps": 0.0,
    }
