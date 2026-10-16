"""Traffic generators for application-oriented SwitchBench experiments."""
from __future__ import annotations
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class AppPacket:
    time: float
    size_bytes: int
    flow_id: str
    app: str
    index: int


def generate_voice(calls: int, duration: float = 5.0, seed: int = 42):
    """20 ms voice frames: 160-byte payload + 40-byte headers = 80 kb/s/call."""
    packets = []
    for call in range(calls):
        t, index = 0.0, 0
        while t < duration:
            packets.append(AppPacket(t, 200, f"call-{call}", "voice", index))
            t += 0.020
            index += 1
    return sorted(packets, key=lambda p: (p.time, p.flow_id, p.index))


def generate_file(size_mb: float = 5.0, packet_bytes: int = 1500):
    """One file split into full-size packets; packets are offered back-to-back."""
    total_bytes = int(size_mb * 1_000_000)
    packets, sent, index = [], 0, 0
    while sent < total_bytes:
        size = min(packet_bytes, total_bytes - sent)
        packets.append(AppPacket(0.0, size, "file-0", "file", index))
        sent += size
        index += 1
    return packets


def generate_interactive(users: int, duration: float = 5.0, seed: int = 42):
    """Users issue 100-byte requests; each gets a 500-byte response 10 ms later."""
    rng = random.Random(seed)
    packets = []
    for user in range(users):
        t, index = 0.0, 0
        while t < duration:
            t += rng.expovariate(1.0)  # mean one second between requests
            if t >= duration:
                break
            flow = f"user-{user}"
            packets.append(AppPacket(t, 100, flow, "interactive_request", index))
            packets.append(AppPacket(t + 0.010, 500, flow, "interactive_response", index))
            index += 1
    return sorted(packets, key=lambda p: (p.time, p.flow_id, p.index, p.app))
