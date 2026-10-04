from .metrics import calculate_metrics
from .models import Packet
from .network import PATHS, default_topology
from .traffic import arrival_times
from .switching.packet_switching import PacketSwitching
from .switching.circuit_switching import CircuitSwitching
from .switching.virtual_circuit import VirtualCircuit


SWITCH_TYPES = ("packet", "circuit", "virtual_circuit")


def run_simulation(switching_type="packet", traffic_rate=10, packet_size=1000, bandwidth=10_000_000,
                   queue_capacity=20, simulation_duration=10, propagation_delay=0.01):
    if switching_type not in SWITCH_TYPES:
        raise ValueError(f"switching_type must be one of {', '.join(SWITCH_TYPES)}")
    if traffic_rate < 0 or packet_size <= 0 or bandwidth <= 0 or queue_capacity < 1 or simulation_duration <= 0 or propagation_delay < 0:
        raise ValueError("Rates/delays must be non-negative and sizes, bandwidth, capacity and duration must be positive")
    nodes, links = default_topology(bandwidth, propagation_delay, queue_capacity)
    packets = [Packet(i, "Source", "Destination", packet_size * 8, t, switching_type) for i, t in enumerate(arrival_times(traffic_rate, simulation_duration))]
    setup_time, strategy = 0.0, None
    if switching_type == "circuit":
        strategy = CircuitSwitching()
        # Connection setup consumes signaling time (one propagation round trip).
        setup_time = 2 * propagation_delay
        path = strategy.establish(PATHS, links, bandwidth)
        for p in packets:
            p.path = path
    elif switching_type == "virtual_circuit":
        strategy = VirtualCircuit()
        setup_time = 2 * propagation_delay
        path = strategy.establish(PATHS)
        for p in packets:
            p.path, p.vc_id = path, strategy.vc_id
    else:
        strategy = PacketSwitching()
        for p in packets:
            p.path = strategy.path_for(p.packet_id, PATHS)

    # Each link has a FIFO queue and a single serializer. Events are processed in
    # arrival order; downstream arrivals include transmission and propagation.
    events = []
    for packet in packets:
        data_ready = max(packet.creation_time, setup_time)
        if data_ready <= simulation_duration:
            events.append((data_ready, packet, 0))
        else:
            packet.dropped = True
    events.sort(key=lambda e: (e[0], e[1].packet_id))
    for now, packet, hop in events:
        for index in range(hop, len(packet.path)):
            link = links[packet.path[index]]
            if not link.queue.push(packet, now):
                break
            start = max(now, link.busy_until)
            tx = packet.size_bits / link.bandwidth
            waiting_ahead = int((link.busy_until - now) / tx) if tx > 0 and link.busy_until > now else 0
            if start > now and waiting_ahead >= queue_capacity:
                packet.dropped = True
                link.queue._items.remove(packet)
                break
            if packet.transmission_start_time is None:
                packet.transmission_start_time = start
            packet.total_queue_delay += start - now
            finish = start + tx
            link.busy_time += tx
            link.busy_until = finish
            # The lightweight event model advances the packet to the next hop.
            now = finish + link.propagation_delay
            packet.queue_exit_time = start
            link.queue._items.remove(packet)
            link.queue.length_samples.append(len(link.queue))
        if not packet.dropped:
            packet.delivery_time = now
    if strategy and switching_type == "circuit":
        strategy.release(links)
    queues = [link.queue for link in links.values()]
    return calculate_metrics(packets, simulation_duration, setup_time, list(links.values()), queues)


def run_comparison(**kwargs):
    return {kind: run_simulation(switching_type=kind, **kwargs) for kind in SWITCH_TYPES}
