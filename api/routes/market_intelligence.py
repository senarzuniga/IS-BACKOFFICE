"""REST API for the web intelligence pipeline."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from backoffice.intelligence.pipeline import TASK_TYPES, pipeline
from backoffice.intelligence.storage import intelligence_db

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])

# Module-level task registry — survives server lifetime
_tasks: Dict[str, Dict[str, Any]] = {}


# ── Request / Response models ─────────────────────────────────────────────────

class IntelligenceRequest(BaseModel):
    task_type:        str
    query:            str
    start_urls:       List[str]
    max_pages:        int = 30
    max_depth:        int = 2
    use_js:           bool = False
    keywords:         Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None


class MonitoringTargetRequest(BaseModel):
    name:         str
    url:          str
    monitor_type: str = "content"   # price | product | content
    config:       Dict[str, Any] = {}


# ── Task helpers ──────────────────────────────────────────────────────────────

def _run_pipeline_task(task_id: str, req: IntelligenceRequest) -> None:
    def cb(msg: str) -> None:
        _tasks[task_id]["progress"].append(msg)

    try:
        result = pipeline.run(
            task_type=req.task_type,
            query=req.query,
            start_urls=req.start_urls,
            max_pages=req.max_pages,
            max_depth=req.max_depth,
            use_js=req.use_js,
            keywords=req.keywords,
            exclude_patterns=req.exclude_patterns,
            progress_callback=cb,
        )
        _tasks[task_id].update({"status": "completed", "result": result})
    except Exception as exc:
        _tasks[task_id].update({"status": "failed", "error": str(exc)})


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/search")
async def start_intelligence_task(
    req: IntelligenceRequest, background_tasks: BackgroundTasks
):
    """Start a deep-crawl intelligence task in the background."""
    if req.task_type not in TASK_TYPES:
        raise HTTPException(
            400, f"task_type inválido. Válidos: {list(TASK_TYPES.keys())}"
        )
    if not req.start_urls:
        raise HTTPException(400, "Se requiere al menos una URL en start_urls")

    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "running", "progress": [], "request": req.model_dump()}
    background_tasks.add_task(_run_pipeline_task, task_id, req)
    return {"task_id": task_id, "status": "started", "task_type": req.task_type}


@router.get("/tasks")
async def list_tasks(limit: int = 20):
    """List recent intelligence tasks (most recent first)."""
    items = list(_tasks.items())[-limit:]
    return [
        {
            "task_id": tid,
            "status":  v.get("status"),
            "query":   v.get("request", {}).get("query", ""),
            "type":    v.get("request", {}).get("task_type", ""),
        }
        for tid, v in reversed(items)
    ]


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status and progress log of a running or completed task."""
    if task_id not in _tasks:
        raise HTTPException(404, "Tarea no encontrada")
    t = dict(_tasks[task_id])
    t.pop("result", None)   # result available via /tasks/{id}/result
    return t


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """Get the full result of a completed task."""
    if task_id not in _tasks:
        raise HTTPException(404, "Tarea no encontrada")
    t = _tasks[task_id]
    if t["status"] != "completed":
        raise HTTPException(400, f"Estado actual: {t['status']}")
    return t.get("result", {})


# ── Data access ────────────────────────────────────────────────────────────────

@router.get("/sessions")
async def get_sessions(task_type: Optional[str] = None, limit: int = 100):
    """List crawl sessions stored in DB."""
    return intelligence_db.get_sessions(task_type=task_type, limit=limit)


@router.get("/market")
async def get_market_intel(
    company: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 200,
):
    """Get stored market intelligence records."""
    return intelligence_db.get_market_intel(company=company, category=category, limit=limit)


@router.get("/leads")
async def get_leads(
    sector: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 500,
):
    """Get stored B2B leads."""
    return intelligence_db.get_leads(sector=sector, country=country, limit=limit)


@router.get("/content")
async def get_content(content_type: Optional[str] = None, limit: int = 200):
    """Get stored content items (news, blogs, trends, …)."""
    return intelligence_db.get_content(content_type=content_type, limit=limit)


# ── Monitoring ─────────────────────────────────────────────────────────────────

@router.post("/monitor")
async def add_monitoring_target(req: MonitoringTargetRequest):
    """Register a URL for continuous monitoring."""
    valid = {"price", "product", "content"}
    if req.monitor_type not in valid:
        raise HTTPException(400, f"monitor_type debe ser uno de: {valid}")
    tid = intelligence_db.save_monitoring_target(
        name=req.name, url=req.url,
        monitor_type=req.monitor_type, config=req.config,
    )
    return {"id": tid, "status": "created"}


@router.get("/monitor/targets")
async def get_monitoring_targets(active_only: bool = True):
    return intelligence_db.get_monitoring_targets(active_only=active_only)


@router.delete("/monitor/targets/{target_id}")
async def deactivate_target(target_id: str):
    intelligence_db.deactivate_monitoring_target(target_id)
    return {"status": "deactivated", "id": target_id}


@router.post("/monitor/run/{target_id}")
async def run_monitoring_check(target_id: str, background_tasks: BackgroundTasks):
    """Trigger an immediate monitoring check for a target."""
    targets = intelligence_db.get_monitoring_targets(active_only=False)
    target = next((t for t in targets if t["id"] == target_id), None)
    if not target:
        raise HTTPException(404, "Target no encontrado")
    background_tasks.add_task(pipeline.run_monitoring_check, target)
    return {"status": "check_started", "target_id": target_id}


@router.get("/monitor/alerts")
async def get_alerts(limit: int = 100):
    return intelligence_db.get_alerts(limit=limit)


# ── Stats & export ─────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats():
    """Return DB row counts for all intelligence tables."""
    return intelligence_db.get_stats()


@router.get("/export/{table}")
async def export_data(table: str, limit: int = 2000):
    """Export a table as JSON (for BI / reporting integration)."""
    data = intelligence_db.export_json(table, limit=limit)
    return PlainTextResponse(data, media_type="application/json")


@router.get("/task-types")
async def list_task_types():
    return TASK_TYPES
