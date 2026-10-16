from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.application_simulation import SWITCH_TYPES, run_application_experiment

LOAD_SWEEPS = {
    "voice": [10, 25, 50, 100, 125, 150, 200],
    "file": [0, 10, 25, 50, 100],  # background calls; zero is allowed by runner below
    "interactive": [1, 5, 10, 25, 50],
}


def run_application_experiments(bandwidth=10_000_000, queue_capacity=20, duration=5.0, file_size_mb=5.0):
    output_dir = ROOT / "results"
    graph_dir = ROOT / "graphs" / "applications"
    output_dir.mkdir(parents=True, exist_ok=True)
    graph_dir.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for app, loads in LOAD_SWEEPS.items():
        rows = []
        for load in loads:
            for kind in SWITCH_TYPES:
                row = run_application_experiment(
                    app, load, kind, bandwidth=bandwidth,
                    queue_capacity=queue_capacity, duration=duration, file_size_mb=file_size_mb)
                row["load"] = load
                rows.append(row)
                all_rows.append(row)
        frame = pd.DataFrame(rows)
        frame.to_csv(output_dir / f"{app}_experiments.csv", index=False)
        _graphs(frame, app, graph_dir)
    combined = pd.DataFrame(all_rows)
    combined.to_csv(output_dir / "application_experiments.csv", index=False)
    return output_dir / "application_experiments.csv"


def _graphs(frame, app, graph_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = {
        "voice": [
            ("average_end_to_end_delay", "Mean end-to-end delay (s)"),
            ("jitter", "Mean absolute delay variation (s)"),
            ("call_blocking_probability", "Call blocking probability"),
            ("packets_lost", "Packets lost"),
        ],
        "file": [
            ("file_completion_time", "File completion time (s)"),
            ("goodput_bps", "Goodput (bit/s)"),
            ("packets_lost", "Packets lost"),
        ],
        "interactive": [
            ("average_response_time", "Mean response time (s)"),
            ("p95_response_time", "95th percentile response time (s)"),
            ("packets_lost", "Packets lost"),
        ],
    }[app]
    for metric, ylabel in metrics:
        fig, ax = plt.subplots()
        for kind, group in frame.groupby("switching_type"):
            ax.plot(group["load"], group[metric], marker="o", label=kind.replace("_", " ").title())
        ax.set_xlabel("Concurrent calls" if app == "voice" else
                      "Background voice calls" if app == "file" else "Interactive users")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{app.title()}: {ylabel} vs load")
        ax.grid(alpha=.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(graph_dir / f"{app}_{metric}.png", dpi=140)
        plt.close(fig)


if __name__ == "__main__":
    print(f"Generated application experiments: {run_application_experiments()}")
