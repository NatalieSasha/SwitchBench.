from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.simulation import SWITCH_TYPES, run_comparison, run_simulation
from experiments.run_experiments import ROOT, TRAFFIC_RATES, run_all_experiments


st.set_page_config(page_title="SWITCHBENCH", page_icon="⌁", layout="wide")
st.title("SWITCHBENCH")
st.caption("Packet, Circuit and Virtual-Circuit Switching Performance Study")
st.markdown(
    """<style>
    .block-container { padding-top: 1.8rem; }
    div[data-testid="stMetric"] { background: #f5f8fb; border: 1px solid #dce3ea;
        padding: 0.8rem 1rem; border-radius: 0.45rem; }
    </style>""",
    unsafe_allow_html=True,
)

MODEL_LABELS = {
    "packet": "Packet Switching",
    "circuit": "Circuit Switching",
    "virtual_circuit": "Virtual-Circuit Switching",
}
METRIC_LABELS = {
    "setup_time": "Setup Time (s)",
    "average_transmission_delay": "Average Transmission Delay (s)",
    "average_queue_delay": "Average Queue Delay (s)",
    "average_end_to_end_delay": "Average End-to-End Delay (s)",
    "packets_generated": "Packets Generated",
    "packets_delivered": "Packets Delivered",
    "packets_lost": "Packets Lost",
    "packet_delivery_ratio": "Packet Delivery Ratio (%)",
    "throughput": "Throughput (bit/s)",
    "resource_utilization": "Resource Utilization (%)",
    "average_queue_length": "Average Queue Length",
}
COMPARISON_METRICS = [
    "setup_time", "average_end_to_end_delay", "average_queue_delay", "packets_lost",
    "packet_delivery_ratio", "throughput", "resource_utilization",
]


def presentation_values(metrics):
    values = dict(metrics)
    values["packet_delivery_ratio"] *= 100
    values["resource_utilization"] *= 100
    return values


def metric_table(metrics):
    values = presentation_values(metrics)
    return pd.DataFrame({"Metric": list(METRIC_LABELS.values()),
                         "Value": [values[key] for key in METRIC_LABELS]})


with st.sidebar:
    st.header("Simulation controls")
    kind = st.selectbox("Switching model", SWITCH_TYPES, format_func=lambda key: MODEL_LABELS[key])
    rate = st.select_slider("Traffic rate (packets/sec)", TRAFFIC_RATES, value=50)
    size = st.number_input("Packet size (bytes)", min_value=1, value=1000)
    bandwidth = st.number_input("Bandwidth (Mbps)", min_value=0.01, value=10.0) * 1_000_000
    capacity = st.number_input("Queue capacity (packets)", min_value=1, value=20)
    duration = st.number_input("Simulation duration (seconds)", min_value=0.1, value=10.0)
    run_one = st.button("RUN SIMULATION", use_container_width=True)
    run_compare = st.button("RUN COMPARISON", use_container_width=True)
    run_full = st.button("RUN FULL EXPERIMENT", use_container_width=True)

params = dict(traffic_rate=rate, packet_size=size, bandwidth=bandwidth,
              queue_capacity=capacity, simulation_duration=duration)
tabs = st.tabs(["Single Simulation", "Comparison", "Experiments"])

with tabs[0]:
    single_signature = (kind, *params.values())
    if run_one or st.session_state.get("single_signature") != single_signature:
        st.session_state.single_result = run_simulation(switching_type=kind, **params)
        st.session_state.single_signature = single_signature
    result = st.session_state.single_result
    st.subheader(MODEL_LABELS[kind])
    display = presentation_values(result)
    card_keys = [
        "setup_time", "average_transmission_delay", "average_queue_delay", "average_end_to_end_delay",
        "packets_generated", "packets_delivered", "packets_lost", "packet_delivery_ratio",
        "throughput", "resource_utilization", "average_queue_length",
    ]
    for offset in range(0, len(card_keys), 4):
        cols = st.columns(4)
        for col, key in zip(cols, card_keys[offset:offset + 4]):
            value = display[key]
            if key in ("packet_delivery_ratio", "resource_utilization"):
                shown = f"{value:.2f}%"
            elif key.startswith("average_") or key == "setup_time":
                shown = f"{value:.6f}"
            elif key == "throughput":
                shown = f"{value:,.2f}"
            elif key == "average_queue_length":
                shown = f"{value:.3f}"
            else:
                shown = f"{value:,}"
            col.metric(METRIC_LABELS[key], shown)
    with st.expander("Compact results table", expanded=True):
        st.dataframe(metric_table(result), hide_index=True, use_container_width=True)

with tabs[1]:
    comparison_signature = tuple(params.values())
    if run_compare or st.session_state.get("comparison_signature") != comparison_signature:
        st.session_state.comparison = run_comparison(**params)
        st.session_state.comparison_signature = comparison_signature
    raw = pd.DataFrame(st.session_state.comparison).T.rename_axis("switching_type").reset_index()
    raw["switching_type"] = raw["switching_type"].map(MODEL_LABELS)
    shown = raw[["switching_type", *COMPARISON_METRICS]].copy()
    shown["packet_delivery_ratio"] *= 100
    shown["resource_utilization"] *= 100
    comparison_labels = {**METRIC_LABELS, "packets_lost": "Packet Loss"}
    shown = shown.rename(columns={"switching_type": "Switching Model", **comparison_labels})
    st.dataframe(shown, hide_index=True, use_container_width=True)
    chart_metrics = [
        ("average_end_to_end_delay", "Average End-to-End Delay (s)"),
        ("average_queue_delay", "Average Queue Delay (s)"),
        ("packets_lost", "Packets Lost"),
        ("packet_delivery_ratio", "Packet Delivery Ratio (%)"),
        ("throughput", "Throughput (bit/s)"),
        ("resource_utilization", "Resource Utilization (%)"),
        ("setup_time", "Setup Time (s)"),
    ]
    chart_cols = st.columns(2)
    for index, (metric, title) in enumerate(chart_metrics):
        chart_data = raw[["switching_type", metric]].copy()
        if metric in ("packet_delivery_ratio", "resource_utilization"):
            chart_data[metric] *= 100
        chart_cols[index % 2].plotly_chart(
            px.bar(chart_data, x="switching_type", y=metric, title=title,
                   labels={"switching_type": "Switching Model", metric: title},
                   color="switching_type", color_discrete_sequence=["#315b7d", "#638a72", "#c08a45"]),
            use_container_width=True,
        )

with tabs[2]:
    csv_path = ROOT / "results" / "experiments.csv"
    if run_full or not csv_path.exists():
        with st.spinner("Running the configured normal-load experiments…"):
            csv_path = run_all_experiments(packet_size=size, bandwidth=bandwidth,
                                           queue_capacity=capacity, simulation_duration=duration)
    frame = pd.read_csv(csv_path)
    frame["switching_type"] = frame["switching_type"].map(MODEL_LABELS)
    st.dataframe(frame.rename(columns={"switching_type": "Switching Model"}), hide_index=True, use_container_width=True)
    st.download_button("Download normal experiment CSV", frame.to_csv(index=False).encode(),
                       "experiments.csv", "text/csv")
    st.subheader("Generated experiment graphs")
    graph_files = [
        ("average_end_to_end_delay.png", "Average End-to-End Delay vs Traffic Rate"),
        ("packets_lost.png", "Packets Lost vs Traffic Rate"),
        ("throughput.png", "Throughput vs Traffic Rate"),
        ("resource_utilization.png", "Resource Utilization vs Traffic Rate"),
        ("setup_time_comparison.png", "Setup Time Comparison"),
    ]
    for offset in range(0, len(graph_files), 2):
        cols = st.columns(2)
        for col, (filename, caption) in zip(cols, graph_files[offset:offset + 2]):
            image_path = ROOT / "graphs" / filename
            if image_path.exists():
                col.image(str(image_path), caption=caption, use_container_width=True)
            else:
                col.info(f"{filename} will be generated when you run the full experiment.")
