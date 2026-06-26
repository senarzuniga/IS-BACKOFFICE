import json
import statistics
import sys
from pathlib import Path
from datetime import datetime

# ensure repo root on path for local imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.consumption_engine import CorrugatorEngineV3
from core.kpi_calculator import calculate_kpis


CONFIG_PATH = Path(__file__).parent.parent / "data" / "config_default.json"
OUT_DIR = Path(__file__).parent.parent / "data" / "benchmarks"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_simulation(cfg, scenario, duration_min=10080, step_min=1.0, sample_interval_min=60, seed=42):
    engine = CorrugatorEngineV3(config=cfg.copy(), scenario=scenario, seed=seed)
    samples = []
    steps = int(duration_min / step_min)
    sample_every = max(1, int(sample_interval_min / step_min))
    for i in range(steps):
        engine.step(step_min)
        if (i + 1) % sample_every == 0:
            kpis = calculate_kpis(engine)
            samples.append({
                "time_min": engine.time,
                "production_meters": engine.metrics.get("production_meters", 0.0),
                "starvation_count": engine.metrics.get("starvation_count", 0),
                "deliveries_scheduled": engine.metrics.get("deliveries_scheduled", 0),
                "deliveries_successful": engine.metrics.get("deliveries_successful", 0),
                "kpis": kpis,
            })

    # aggregates
    total_production = engine.metrics.get("production_meters", 0.0)
    starvation = engine.metrics.get("starvation_count", 0)
    scheduled = engine.metrics.get("deliveries_scheduled", 0)
    successful = engine.metrics.get("deliveries_successful", 0)
    delivery_rate = (successful / scheduled * 100.0) if scheduled > 0 else 100.0

    avg_kpis = {}
    if samples:
        for key in samples[0]["kpis"].keys():
            avg_kpis[key] = statistics.mean(s["kpis"][key] for s in samples)
    else:
        avg_kpis = {"track_saturation": 0.0, "RRI": 0.0, "PSS": 0.0, "LPI": 0.0, "OEE": 0.0}

    result = {
        "scenario": scenario,
        "total_production_m": total_production,
        "production_m_per_h": total_production / (duration_min / 60.0),
        "starvation_count": starvation,
        "deliveries_scheduled": scheduled,
        "deliveries_successful": successful,
        "delivery_success_rate_pct": delivery_rate,
        "avg_kpis": avg_kpis,
        "samples": samples,
    }
    return result


def estimate_costs(cfg, summary, scenario):
    hours = 7 * 24
    # labor cost: forklift only for scenario A
    forklift_hours = hours if scenario == "A" else 0
    num_forklifts = cfg.get("num_forklifts", 1)
    labor_cost = cfg.get("forklift_operator_cost", 35.0) * num_forklifts * forklift_hours

    # maintenance prorated weekly
    maint_forklift_week = cfg.get("maintenance_cost_forklift", 12000) / 52.0
    maint_ingetrans_week = cfg.get("maintenance_cost_ingetrans", 4000) / 52.0
    maintenance = maint_forklift_week if scenario == "A" else maint_ingetrans_week

    # starvation costs
    starvation_cost = cfg.get("cost_per_starvation_event", 150.0) * summary.get("starvation_count", 0)

    # downtime minutes estimate: assume 5 min per starvation
    downtime_min = summary.get("starvation_count", 0) * 5
    downtime_cost = downtime_min * cfg.get("cost_of_corrugator_downtime", 45.0)

    # capex amortization weekly for ingetrans
    ingetrans_capex = cfg.get("ingetrans_capex", 1400000)
    amort_years = cfg.get("ingetrans_life_years", 10)
    amort_week = (ingetrans_capex / (amort_years * 52.0)) if scenario == "B" else 0.0

    total_operational = labor_cost + maintenance + starvation_cost + downtime_cost + amort_week
    return {
        "labor_cost": labor_cost,
        "maintenance": maintenance,
        "starvation_cost": starvation_cost,
        "downtime_min": downtime_min,
        "downtime_cost": downtime_cost,
        "amortization_week": amort_week,
        "total_operational_cost_week": total_operational,
    }


def main():
    cfg = json.load(open(CONFIG_PATH, "r", encoding="utf-8"))
    # set realistic assumptions for week (2 shifts/day, but corrugator runs continuously)
    duration_min = 7 * 24 * 60

    print("Running weekly simulation (7 days, 2 shifts/day implied)\n")

    res_A = run_simulation(cfg, "A", duration_min=duration_min, step_min=1.0, sample_interval_min=60, seed=101)
    res_B = run_simulation(cfg, "B", duration_min=duration_min, step_min=1.0, sample_interval_min=60, seed=101)

    costs_A = estimate_costs(cfg, res_A, "A")
    costs_B = estimate_costs(cfg, res_B, "B")

    # comparative metrics
    production_diff = res_B["total_production_m"] - res_A["total_production_m"]
    cost_diff = costs_B["total_operational_cost_week"] - costs_A["total_operational_cost_week"]
    cost_per_extra_m = (cost_diff / production_diff) if production_diff != 0 else None

    summary = {
        "run_at": datetime.utcnow().isoformat() + "Z",
        "config": cfg,
        "scenario_A": res_A,
        "scenario_B": res_B,
        "costs_A": costs_A,
        "costs_B": costs_B,
        "comparison": {
            "production_diff_m": production_diff,
            "cost_diff_eur": cost_diff,
            "cost_per_extra_m": cost_per_extra_m,
        },
    }

    out_file = OUT_DIR / f"weekly_compare_{int(datetime.utcnow().timestamp())}.json"
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    # pretty print summary
    print("Summary (weekly):")
    for sname in ("scenario_A", "scenario_B"):
        s = summary[sname]
        print(f"\n{sname} (scenario={s['scenario']}):")
        print(f"  Total production (m): {s['total_production_m']:.1f}")
        print(f"  Production (m/h): {s['production_m_per_h']:.1f}")
        print(f"  Starvation events: {s['starvation_count']}")
        print(f"  Deliveries scheduled/successful: {s['deliveries_scheduled']}/{s['deliveries_successful']} ({s['delivery_success_rate_pct']:.1f}%)")
        ak = s['avg_kpis']
        print(f"  Avg KPIs - OEE: {ak['OEE']:.1f}%, LPI: {ak['LPI']:.1f}, RRI: {ak['RRI']:.2f}, PSS: {ak['PSS']:.1f}%")
        c = summary['costs_A'] if sname == 'scenario_A' else summary['costs_B']
        print(f"  Estimated weekly operational cost (EUR): {c['total_operational_cost_week']:.2f}")

    print("\nComparison:")
    print(f"  Production difference (B - A) m: {summary['comparison']['production_diff_m']:.1f}")
    print(f"  Cost difference (B - A) EUR/week: {summary['comparison']['cost_diff_eur']:.2f}")
    if summary['comparison']['cost_per_extra_m'] is not None:
        print(f"  Cost per extra meter (EUR/m): {summary['comparison']['cost_per_extra_m']:.6f}")
    print(f"\nSaved JSON: {out_file.resolve()}")


if __name__ == "__main__":
    main()
