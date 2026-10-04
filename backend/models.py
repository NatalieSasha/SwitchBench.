from dataclasses import dataclass
from typing import Optional


@dataclass
class Packet:
    packet_id: int
    source: str
    destination: str
    size_bits: int
    creation_time: float
    switching_type: str
    queue_enter_time: Optional[float] = None
    queue_exit_time: Optional[float] = None
    transmission_start_time: Optional[float] = None
    delivery_time: Optional[float] = None
    dropped: bool = False
    path: tuple[str, ...] = ()
    vc_id: Optional[int] = None
    total_queue_delay: float = 0.0

    @property
    def queuing_delay(self) -> float:
        return max(0.0, (self.queue_exit_time or 0.0) - (self.queue_enter_time or 0.0)) if self.queue_enter_time is not None and self.queue_exit_time is not None else 0.0

    @property
    def transmission_delay(self) -> float:
        return max(0.0, (self.delivery_time or 0.0) - (self.transmission_start_time or 0.0)) if self.transmission_start_time is not None and self.delivery_time is not None else 0.0

    @property
    def end_to_end_delay(self) -> float:
        return max(0.0, self.delivery_time - self.creation_time) if self.delivery_time is not None else 0.0
