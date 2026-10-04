from collections import deque
from dataclasses import dataclass, field
from typing import Deque

from .models import Packet


@dataclass
class Node:
    name: str


@dataclass
class Router(Node):
    forwarding_table: dict = field(default_factory=dict)


class PacketQueue:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._items: Deque[Packet] = deque()
        self.length_samples: list[int] = []

    def push(self, packet: Packet, now: float) -> bool:
        packet.queue_enter_time = now
        if len(self._items) >= self.capacity:
            packet.dropped = True
            return False
        self._items.append(packet)
        self.length_samples.append(len(self._items))
        return True

    def pop(self, now: float) -> Packet:
        packet = self._items.popleft()
        packet.queue_exit_time = now
        return packet

    def __len__(self) -> int:
        return len(self._items)

    @property
    def average_length(self) -> float:
        return sum(self.length_samples) / len(self.length_samples) if self.length_samples else 0.0


@dataclass
class Link:
    name: str
    bandwidth: float
    propagation_delay: float
    capacity: int
    busy_until: float = 0.0
    reserved_by: str | None = None
    busy_time: float = 0.0
    queue: PacketQueue = field(init=False)

    def __post_init__(self):
        self.queue = PacketQueue(self.capacity)


def default_topology(bandwidth: float, propagation_delay: float, capacity: int):
    # Two equal-cost paths; packet routing selects a path per packet.
    nodes = {n: Node(n) for n in ("Source", "Router 1", "Router 2", "Router 3", "Destination")}
    links = {
        "s-r1": Link("s-r1", bandwidth, propagation_delay, capacity),
        "r1-r2": Link("r1-r2", bandwidth, propagation_delay, capacity),
        "r1-r3": Link("r1-r3", bandwidth, propagation_delay, capacity),
        "r2-d": Link("r2-d", bandwidth, propagation_delay, capacity),
        "r3-d": Link("r3-d", bandwidth, propagation_delay, capacity),
    }
    return nodes, links


PATHS = (("s-r1", "r1-r2", "r2-d"), ("s-r1", "r1-r3", "r3-d"))
