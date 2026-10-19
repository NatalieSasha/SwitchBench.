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


## Application-specific experiments (added)

The application experiment layer adds traffic patterns for voice, file transfer, and interactive request/response workloads.

- `backend/applications.py`: deterministic voice, file, and interactive packet generators.
- `backend/application_simulation.py`: application-level metrics and the simplified comparison model.
- `experiments/run_application_experiments.py`: load sweeps, per-application CSV files, and graphs.
- `frontend/app.py`: an **Application Experiments** tab with an application selector and controls.

Run from the project root in PowerShell:

```powershell
python -m pip install -r requirements.txt
python -m experiments.run_application_experiments
```

Generated files:
- `results/voice_experiments.csv`
- `results/file_experiments.csv`
- `results/interactive_experiments.csv`
- `results/application_experiments.csv`
- `graphs/applications/` (PNG graphs)

The default sweeps are voice calls `[10, 25, 50, 100, 125, 150, 200]`, file transfer with `[0, 10, 25, 50, 100]` background voice calls, and interactive users `[1, 5, 10, 25, 50]`. Each load is run for packet, circuit, and virtual-circuit switching.

### Model assumptions and interpretation

These are simplified educational experiments, not a full TCP/IP implementation or a calibrated network simulator. Voice uses 200-byte packets every 20 ms (160-byte payload plus 40 bytes of assumed headers), equivalent to 80 kb/s per call. Circuit voice admission reserves 80 kb/s per admitted call, so the theoretical call capacity is `floor(link bandwidth / 80,000)`. Circuit voice delay is fixed in this model and admitted calls have zero modeled jitter. Packet and virtual-circuit traffic use shared link-availability clocks and a waiting-time-based queue overflow approximation.

The file experiment models one 5 MB file. Packet and virtual-circuit cases add the selected number of background voice calls. To keep the model simple, the circuit file case gives the file a dedicated circuit after setup and does **not** multiplex the background calls onto that same circuit. Interactive traffic models a 100-byte request and a 500-byte response 10 ms later, with a mean inter-request interval of one second per user. The current model does not implement true packet reordering, TCP congestion control, retransmission, or a complete event queue; `out_of_order_count` is therefore reported as zero rather than claiming reordering that was not simulated.


