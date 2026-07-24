from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class SimulationJobClient:
    """Thin client for simulator job API used by Workbenches."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.environ.get("SIMULATOR_API_URL", "http://localhost:8000")

    def submit(self, scenario: str, duration_s: int, tick_s: float = 1.0, seed: int = 42) -> Dict[str, Any]:
        payload = {
            "scenario": scenario,
            "duration_s": int(duration_s),
            "tick_s": float(tick_s),
            "seed": int(seed),
        }
        try:
            resp = requests.post(f"{self.base_url}/run", json=payload, timeout=10)
        except requests.RequestException as e:
            return {"error": "api_unreachable", "exc": str(e)}
        if resp.status_code != 200:
            return {"error": "api_error", "status_code": resp.status_code, "text": resp.text}
        body = resp.json()
        return {"job_id": body.get("job_id")}

    def poll(self, job_id: str, timeout_s: int = 600, sleep_s: float = 1.0) -> Dict[str, Any]:
        start = time.time()
        while True:
            try:
                r = requests.get(f"{self.base_url}/status/{job_id}", timeout=10)
            except requests.RequestException as e:
                return {"error": "poll_error", "exc": str(e)}
            if r.status_code != 200:
                if time.time() - start > timeout_s:
                    return {"error": "timeout", "detail": f"poll timeout after {timeout_s}s"}
                time.sleep(sleep_s)
                continue
            data = r.json()
            status = data.get("status")
            if status == "finished":
                return data.get("result", {})
            if status == "failed":
                return {"error": "job_failed", "detail": data.get("error")}
            if time.time() - start > timeout_s:
                return {"error": "timeout", "detail": f"poll timeout after {timeout_s}s"}
            time.sleep(sleep_s)


def load_run_summaries(outputs_dir: Path, filename: str = "run_summary.json") -> List[Dict[str, Any]]:
    if not outputs_dir.exists():
        return []
    runs = sorted([p for p in outputs_dir.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    summaries: List[Dict[str, Any]] = []
    for run in runs:
        p = run / filename
        if not p.exists():
            continue
        try:
            summaries.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return summaries
