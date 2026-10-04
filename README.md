# SwitchBench

**Packet, Circuit and Virtual-Circuit Switching Performance Study**

SwitchBench is a small reproducible Computer Networks course project. It models a source, a router with two branches, and a destination, and compares three forwarding approaches using the same seeded traffic arrivals and physical parameters. The simulator uses a discrete-event style link availability clock, FIFO queue objects, packet serialization time, and propagation delay. It is educational and does not model a full IP stack or a packet-level protocol implementation.

## Problem statement and objectives

Compare the impact of connection setup, resource sharing, queueing, and forwarding state on delay, loss, throughput, and utilization. Packet switching selects a route independently per packet and has no setup. Circuit switching establishes a connection, checks and reserves a route's links, transmits only after setup, and releases reservations. Virtual-circuit switching establishes a VC ID and forwarding table and keeps every packet on the VC's logical route.

## Architecture

`backend/models.py` defines packets; `backend/network.py` defines nodes, links and bounded FIFO queues. `backend/simulation.py` generates seeded Poisson arrivals and drives the link serialization/propagation model. Switching setup behavior is separated into `backend/switching/`. FastAPI exposes the engine; Streamlit presents the same engine and experiment output. `experiments/run_experiments.py` runs all seven rates across the three models and writes CSV and plots.

## Metrics

The API returns setup time, average transmission, queue and end-to-end delay, generated/delivered/lost packets, delivery ratio, throughput in bits/second, resource utilization, and sampled queue length. Throughput is delivered bits divided by configured duration. Transmission service time is packet bits divided by link bits/second; propagation is modeled separately. Circuit and VC setup time is two configured propagation delays. Queue overflow is available in the bounded queue model; offered rates in the defaults are modest relative to a 10 Mbps link, so losses are not guaranteed in every default run.

## Installation

Python 3.11 or later is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

From the repository root:

```powershell
uvicorn backend.main:app --reload
streamlit run frontend/app.py
python experiments/run_experiments.py
pytest
```

The API docs are at `http://127.0.0.1:8000/docs`; the dashboard is at `http://localhost:8501`. Experiment execution creates `results/experiments.csv` plus PNG plots in `graphs/`.

## API examples

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod -Method Post http://127.0.0.1:8000/simulate -ContentType 'application/json' -Body '{"switching_type":"packet","traffic_rate":50,"packet_size":1000,"bandwidth":10000000,"queue_capacity":20,"simulation_duration":10}'
Invoke-RestMethod -Method Post http://127.0.0.1:8000/compare -ContentType 'application/json' -Body '{"traffic_rate":50,"packet_size":1000,"bandwidth":10000000,"queue_capacity":20,"simulation_duration":10}'
Invoke-RestMethod -Method Post http://127.0.0.1:8000/experiments -ContentType 'application/json' -Body '{}'
```

Accepted switching types are `packet`, `circuit`, and `virtual_circuit`. Bandwidth is expressed in bits/second.

## Project structure

```text
backend/             API, models, network, metrics, simulation and strategies
frontend/app.py      Streamlit dashboard
experiments/         Full experiment runner and graph generation
results/             Generated experiment CSV
graphs/              Generated experiment graphs
tests/               pytest coverage for packets, queues and switching
requirements.txt
```

Results are generated at run time from the simulator; no experimental values are embedded in the project.
