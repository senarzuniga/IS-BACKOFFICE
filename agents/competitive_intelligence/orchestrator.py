import os
import json
import uuid
import datetime
from typing import Optional, List, Dict, Any

from .market_intelligence_agent import MarketIntelligenceAgent
from .benchmark_agent import BenchmarkAgent
from .executive_strategy_agent import ExecutiveStrategyAgent


def _jobs_dir(root: Optional[str] = None) -> str:
    root = root or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    d = os.path.join(root, "data", "competitive_intelligence", "jobs")
    os.makedirs(d, exist_ok=True)
    return d


def run_job(company: str, seeds: Optional[List[str]] = None, no_web: bool = False, job_id: Optional[str] = None) -> Dict[str, Any]:
    job_id = job_id or str(uuid.uuid4())
    job = {"id": job_id, "company": company, "started_at": datetime.datetime.utcnow().isoformat() + "Z", "status": "running", "steps": []}
    jd = _jobs_dir()
    job_file = os.path.join(jd, f"{job_id}.json")
    with open(job_file, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)

    market = MarketIntelligenceAgent()
    job["steps"].append({"step": "market_intelligence", "status": "running"})
    with open(job_file, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)
    profile = market.run(company, seeds=seeds, no_web=no_web)
    job["steps"][-1]["status"] = "done"
    with open(job_file, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)

    bench = BenchmarkAgent()
    job["steps"].append({"step": "benchmark", "status": "running"})
    with open(job_file, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)
    benchmark = bench.run(profile, {})
    job["steps"][-1]["status"] = "done"
    with open(job_file, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)

    exec_agent = ExecutiveStrategyAgent()
    job["steps"].append({"step": "synthesis", "status": "running"})
    with open(job_file, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)
    report_path = exec_agent.run(company, profile, benchmark)
    job["steps"][-1]["status"] = "done"
    job["status"] = "finished"
    job["finished_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    job["report"] = report_path
    with open(job_file, "w", encoding="utf-8") as fh:
        json.dump(job, fh, indent=2)

    return {"job": job, "profile": profile, "benchmark": benchmark, "report": report_path}
