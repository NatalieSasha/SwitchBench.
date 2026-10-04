from pathlib import Path
import argparse
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.simulation import SWITCH_TYPES, run_simulation

TRAFFIC_RATES = [10, 25, 50, 75, 100, 150, 200]
STRESS_TRAFFIC_RATES = [500, 1000, 1500, 2000, 3000]


def run_all_experiments(packet_size=1000, bandwidth=10_000_000, queue_capacity=20, simulation_duration=10):
    rows = []
    for rate in TRAFFIC_RATES:
        for kind in SWITCH_TYPES:
            rows.append({"traffic_rate": rate, "switching_type": kind, **run_simulation(
                switching_type=kind, traffic_rate=rate, packet_size=packet_size, bandwidth=bandwidth,
                queue_capacity=queue_capacity, simulation_duration=simulation_duration)})
    path = ROOT / "results" / "experiments.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    create_graphs(pd.DataFrame(rows))
    return path


def run_stress_experiments(packet_size=1000, bandwidth=10_000_000, queue_capacity=20, simulation_duration=10):
    """Run a separate high-load sweep with the same topology and simulator."""
    rows = []
    for rate in STRESS_TRAFFIC_RATES:
        for kind in SWITCH_TYPES:
            rows.append({"traffic_rate": rate, "switching_type": kind, **run_simulation(
                switching_type=kind, traffic_rate=rate, packet_size=packet_size, bandwidth=bandwidth,
                queue_capacity=queue_capacity, simulation_duration=simulation_duration)})
    frame = pd.DataFrame(rows)
    path = ROOT / "results" / "stress_experiments.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    create_stress_graphs(frame)
    return path


def create_stress_graphs(frame):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    graph_dir = ROOT / "graphs"
    graph_dir.mkdir(exist_ok=True)
    charts = [
        ("average_end_to_end_delay", "Stress Average End-to-End Delay vs Traffic Rate", "seconds", "stress_average_end_to_end_delay.png"),
        ("packets_lost", "Stress Packets Lost vs Traffic Rate", "packets", "stress_packets_lost.png"),
        ("throughput", "Stress Throughput vs Traffic Rate", "bits/second", "stress_throughput.png"),
        ("resource_utilization", "Stress Resource Utilization vs Traffic Rate", "fraction", "stress_resource_utilization.png"),
    ]
    for metric, title, ylabel, filename in charts:
        fig, ax = plt.subplots()
        for kind, group in frame.groupby("switching_type"):
            ax.plot(group.traffic_rate, group[metric], marker="o", label=kind.replace("_", " ").title())
        ax.set(title=title, xlabel="Traffic rate (packets/second)", ylabel=ylabel)
        ax.grid(alpha=.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(graph_dir / filename, dpi=140)
        plt.close(fig)


def create_graphs(frame):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    graph_dir = ROOT / "graphs"
    graph_dir.mkdir(exist_ok=True)
    charts = [("average_end_to_end_delay", "Average Delay vs Traffic Rate", "seconds"),
              ("packets_lost", "Packet Loss vs Traffic Rate", "packets"),
              ("throughput", "Throughput vs Traffic Rate", "bits/second"),
              ("resource_utilization", "Resource Utilization vs Traffic Rate", "fraction")]
    for metric, title, ylabel in charts:
        fig, ax = plt.subplots()
        for kind, group in frame.groupby("switching_type"):
            ax.plot(group.traffic_rate, group[metric], marker="o", label=kind.replace("_", " ").title())
        ax.set(title=title, xlabel="Traffic rate (packets/second)", ylabel=ylabel)
        ax.grid(alpha=.25); ax.legend(); fig.tight_layout()
        fig.savefig(graph_dir / (metric + ".png"), dpi=140); plt.close(fig)
    fig, ax = plt.subplots()
    latest = frame[frame.traffic_rate == frame.traffic_rate.min()]
    ax.bar(latest.switching_type, latest.setup_time)
    ax.set(title="Setup Time Comparison", ylabel="seconds"); fig.tight_layout()
    fig.savefig(graph_dir / "setup_time_comparison.png", dpi=140); plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SwitchBench normal-load or stress experiments")
    parser.add_argument("--stress", action="store_true", help="run the separate high-load traffic sweep")
    args = parser.parse_args()
    if args.stress:
        print(f"Generated actual stress simulation results: {run_stress_experiments()}")
    else:
        print(f"Generated actual simulation results: {run_all_experiments()}")
