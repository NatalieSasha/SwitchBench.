from statistics import mean


def calculate_metrics(packets, duration, setup_time, links, queues):
    generated = len(packets)
    delivered = [p for p in packets if p.delivery_time is not None and not p.dropped]
    lost = generated - len(delivered)
    return {
        "setup_time": float(setup_time),
        "average_transmission_delay": mean([p.transmission_delay for p in delivered]) if delivered else 0.0,
        "average_queue_delay": mean([p.total_queue_delay for p in delivered]) if delivered else 0.0,
        "average_end_to_end_delay": mean([p.end_to_end_delay for p in delivered]) if delivered else 0.0,
        "packets_generated": generated,
        "packets_delivered": len(delivered),
        "packets_lost": lost,
        "packet_delivery_ratio": len(delivered) / generated if generated else 0.0,
        "throughput": sum(p.size_bits for p in delivered) / duration if duration > 0 else 0.0,
        "resource_utilization": sum(min(link.busy_time, duration) for link in links) / (len(links) * duration) if links and duration > 0 else 0.0,
        "average_queue_length": mean([q.average_length for q in queues]) if queues else 0.0,
    }
