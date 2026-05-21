"""FastAPI routes for Corrugated Plant Simulator (CPS).

Endpoints:
  POST /simulation/config      — Create and save a simulation config
  POST /simulation/run         — Run Python simulation engine
  POST /simulation/optimize    — Multi-scenario optimization
  GET  /simulation/{sim_id}/report?format=pdf|excel  — Download report
  GET  /simulation/scenarios   — Demo scenario catalog
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

# ---- Path setup: allow import from ingecart-marketing-kit ----
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MKT_KIT = _REPO_ROOT / "ingecart-marketing-kit"
if str(_MKT_KIT) not in sys.path:
    sys.path.insert(0, str(_MKT_KIT))

from plant_simulator.config_agent import ConfigAgent
from plant_simulator.simulation_engine import SimulationEngine, ScenarioOptimizer
from plant_simulator.report_generator import generate_excel_report, generate_pdf_report

router = APIRouter(prefix="/simulation", tags=["Plant Simulator"])

agent = ConfigAgent()

# In-memory store for simulation configs and results
_SIM_STORE: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class SimConfigRequest(BaseModel):
    """Flat answers dict from the ConfigAgent wizard."""
    answers: Dict[str, Any] = Field(..., description="Key-value wizard answers")
    name: Optional[str] = Field(None, description="Optional friendly name")


class SimRunRequest(BaseModel):
    sim_id: str = Field(..., description="ID returned by POST /simulation/config")


class SimOptimizeRequest(BaseModel):
    sim_id: str = Field(..., description="ID returned by POST /simulation/config")


class SimConfigResponse(BaseModel):
    sim_id: str
    name: str
    plant_type: str
    num_converters: int
    created_at: str


class SimRunResponse(BaseModel):
    sim_id: str
    plant_name: str
    plant_type: str
    duration_hours: float
    m2_produced: float
    total_units_converted: float
    corrugator_efficiency: float
    average_oee: float
    buffer_avg_occupancy: float
    transport_utilization: float
    recommendations: List[str]
    bottlenecks: List[Dict[str, Any]]
    machine_metrics: List[Dict[str, Any]]


class ScenarioResult(BaseModel):
    scenario_label: str
    m2_produced: float
    total_units_converted: float
    average_oee: float
    corrugator_efficiency: float
    buffer_avg_occupancy: float
    transport_utilization: float


class SimOptimizeResponse(BaseModel):
    sim_id: str
    scenarios: List[ScenarioResult]
    best_scenario: str
    best_oee: float


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/config", response_model=SimConfigResponse, status_code=201)
def create_sim_config(req: SimConfigRequest) -> SimConfigResponse:
    """Create a PlantConfig from wizard answers and store it."""
    try:
        config = agent.build_config(req.answers)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid answers: {exc}") from exc

    sim_id = str(uuid.uuid4())[:8]
    if req.name:
        config.name = req.name

    _SIM_STORE[sim_id] = {
        "config": config,
        "answers": req.answers,
        "results": None,
        "scenario_results": None,
        "created_at": datetime.now().isoformat(),
    }

    return SimConfigResponse(
        sim_id=sim_id,
        name=config.name,
        plant_type=config.plant_type.value,
        num_converters=len(config.converters),
        created_at=_SIM_STORE[sim_id]["created_at"],
    )


@router.post("/run", response_model=SimRunResponse)
def run_simulation(req: SimRunRequest) -> SimRunResponse:
    """Run the Python simulation engine for a stored config."""
    entry = _SIM_STORE.get(req.sim_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"sim_id '{req.sim_id}' not found")

    config = entry["config"]
    try:
        engine = SimulationEngine(config)
        results = engine.run()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation error: {exc}") from exc

    entry["results"] = results

    return SimRunResponse(
        sim_id=req.sim_id,
        plant_name=results.plant_name,
        plant_type=results.plant_type,
        duration_hours=results.duration_hours,
        m2_produced=round(results.m2_produced, 0),
        total_units_converted=round(results.total_units_converted, 0),
        corrugator_efficiency=round(results.corrugator_efficiency, 2),
        average_oee=round(results.average_oee, 2),
        buffer_avg_occupancy=round(results.buffer_avg_occupancy, 2),
        transport_utilization=round(results.transport_utilization, 2),
        recommendations=results.recommendations,
        bottlenecks=[
            {
                "location": b.location,
                "type": b.type,
                "avg_wait_s": b.avg_wait_s,
                "max_wait_s": b.max_wait_s,
                "frequency": b.frequency,
            }
            for b in results.bottlenecks
        ],
        machine_metrics=[
            {
                "machine_id": m.machine_id,
                "availability": m.availability,
                "performance": m.performance,
                "quality": m.quality,
                "oee": m.oee,
                "units_produced": m.units_produced,
                "blocked_time_s": m.blocked_time_s,
                "setup_time_s": m.setup_time_s,
            }
            for m in results.machine_metrics
        ],
    )


@router.post("/optimize", response_model=SimOptimizeResponse)
def optimize_simulation(req: SimOptimizeRequest) -> SimOptimizeResponse:
    """Run 5-scenario optimization for a stored config."""
    entry = _SIM_STORE.get(req.sim_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"sim_id '{req.sim_id}' not found")

    config = entry["config"]
    try:
        optimizer = ScenarioOptimizer()
        sc_results = optimizer.run_all(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Optimization error: {exc}") from exc

    entry["scenario_results"] = sc_results

    best = max(sc_results, key=lambda r: r.average_oee)
    scenarios = [
        ScenarioResult(
            scenario_label=r.scenario_label,
            m2_produced=round(r.m2_produced, 0),
            total_units_converted=round(r.total_units_converted, 0),
            average_oee=round(r.average_oee, 2),
            corrugator_efficiency=round(r.corrugator_efficiency, 2),
            buffer_avg_occupancy=round(r.buffer_avg_occupancy, 2),
            transport_utilization=round(r.transport_utilization, 2),
        )
        for r in sc_results
    ]
    return SimOptimizeResponse(
        sim_id=req.sim_id,
        scenarios=scenarios,
        best_scenario=best.scenario_label,
        best_oee=round(best.average_oee, 2),
    )


@router.get("/{sim_id}/report")
def download_report(
    sim_id: str,
    format: Literal["pdf", "excel"] = "pdf",
) -> Response:
    """Download a PDF or Excel report for a completed simulation."""
    entry = _SIM_STORE.get(sim_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"sim_id '{sim_id}' not found")

    results = entry.get("results")
    if results is None:
        raise HTTPException(
            status_code=400,
            detail="No simulation results found. Run POST /simulation/run first.",
        )

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    base_name = results.plant_name.replace(" ", "_")

    if format == "pdf":
        try:
            data = generate_pdf_report(results)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}") from exc
        return Response(
            content=data,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="CPS_{base_name}_{ts}.pdf"'},
        )
    else:
        try:
            data = generate_excel_report(results)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Excel generation failed: {exc}") from exc
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="CPS_{base_name}_{ts}.xlsx"'},
        )


@router.get("/scenarios/demo")
def get_demo_scenarios() -> List[Dict[str, Any]]:
    """Return the list of pre-built demo scenarios."""
    demos = agent.demo_scenarios()
    return [{"label": label, "answers": dict(answers)} for label, answers in demos]


@router.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "module": "plant_simulator", "stored_sims": str(len(_SIM_STORE))}
