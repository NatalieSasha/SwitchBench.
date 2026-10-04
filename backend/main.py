from pathlib import Path
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .simulation import run_comparison, run_simulation

app = FastAPI(title="SwitchBench API", version="1.0.0")


class SimulationRequest(BaseModel):
    switching_type: str = "packet"
    traffic_rate: float = Field(10, ge=0)
    packet_size: int = Field(1000, gt=0)
    bandwidth: float = Field(10_000_000, gt=0, description="bits per second")
    queue_capacity: int = Field(20, gt=0)
    simulation_duration: float = Field(10, gt=0)


@app.get("/")
def root():
    return {"name": "SwitchBench", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/simulate")
def simulate(request: SimulationRequest):
    try:
        return run_simulation(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/compare")
def compare(request: SimulationRequest):
    params = request.model_dump(exclude={"switching_type"})
    try:
        return run_comparison(**params)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/experiments")
def experiments(request: SimulationRequest):
    from experiments.run_experiments import run_all_experiments
    path = run_all_experiments(packet_size=request.packet_size, bandwidth=request.bandwidth,
                               queue_capacity=request.queue_capacity, simulation_duration=request.simulation_duration)
    frame = pd.read_csv(path)
    return {"rows": len(frame), "result_file": str(path), "traffic_rates": sorted(frame.traffic_rate.unique().tolist())}
