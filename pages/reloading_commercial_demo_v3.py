import io
import json
import sys
import time
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from core.consumption_engine import CorrugatorEngineV3
from core.kpi_calculator import calculate_kpis
from utils.charts import flow_chart, saturation_chart, oee_chart
from utils.renderer_svg_advanced import render_plant_svg


CONFIG_PATH = Path(__file__).parent.parent / "data" / "config_default.json"


def load_defaults() -> Dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def number_widget(key: str, value, uid: str | None = None):
    """Create a number/text input with a stable unique `key` to avoid Streamlit duplicate-id errors.

    `uid` is a prefix (e.g., group name) used to make the widget key unique.
    """
    widget_key = f"{uid}__{key}" if uid else key
    if isinstance(value, int):
        return st.number_input(key, value=value, step=1, key=widget_key)
    try:
        # floats
        return st.number_input(key, value=float(value), key=widget_key)
    except Exception:
        return st.text_input(key, value=str(value), key=widget_key)


def sidebar_config(defaults: Dict) -> Dict:
    st.sidebar.title("Configuración")
    cfg: Dict = {}

    # Group variables by rough categories for readability
    groups = {
        "Plant Geometry & Layout": [
            "num_roll_stands",
            "tracks_per_roll_stand",
            "num_tracks",
            "avg_track_length",
            "exchange_to_track_load",
            "exchange_to_track_return",
            "transfer_travel_length",
            "reel_staging_capacity",
        ],
        "Production Orders": [
            "avg_order_length",
            "min_order_length",
            "max_order_length",
            "short_orders_ratio",
            "medium_orders_ratio",
            "long_orders_ratio",
            "avg_reel_consumption_rate",
            "corrugator_avg_speed",
            "paper_grades_managed",
        ],
        "Reel Characteristics": [
            "max_reel_diameter",
            "avg_reel_diameter",
            "min_reel_diameter",
            "avg_reel_weight",
            "max_reel_weight",
            "avg_reel_width",
            "avg_reel_remaining_at_return",
            "avg_reel_length",
        ],
        "Forklift (Scenario A)": [
            "num_forklifts",
            "forklift_loaded_speed",
            "forklift_empty_speed",
            "forklift_pickup_time",
            "forklift_dropoff_time",
            "avg_search_time",
            "avg_waiting_time",
            "avg_maneuver_time",
            "shift_change_delay",
            "break_duration",
            "break_frequency",
            "forklift_availability",
            "forklift_mtbf",
            "forklift_mttr",
            "wrong_reel_probability",
            "damaged_reel_probability",
            "urgent_orders_per_shift",
            "blocked_track_probability",
            "warehouse_delay_probability",
            "reel_return_frequency",
            "operator_absence_probability",
            "maintenance_events_per_month",
            "forklift_operator_cost",
            "maintenance_cost_forklift",
            "forklift_extra_delay_s",
        ],
        "INGETRANS (Scenario B)": [
            "transfer_pickup_reel",
            "transfer_dropoff_reel",
            "transfer_acceleration_ramp",
            "transfer_deceleration_ramp",
            "transfer_start_stop_overhead",
            "transfer_max_speed",
            "transfer_capacity",
        ],
        "Costs & ROI": [
            "forklift_operator_cost",
            "maintenance_cost_forklift",
            "maintenance_cost_ingetrans",
            "electricity_cost",
            "cost_of_corrugator_downtime",
            "cost_per_starvation_event",
            "cost_per_wrong_reel_event",
            "ingetrans_capex",
            "ingetrans_life_years",
        ],
    }

    for group_name, keys in groups.items():
        with st.sidebar.expander(group_name, expanded=(group_name == "Plant Geometry & Layout")):
            for k in keys:
                if k in defaults:
                    cfg[k] = number_widget(k, defaults[k], uid=group_name.replace(" ", "_"))

    st.sidebar.markdown("---")
    cfg["scenario_select"] = st.sidebar.selectbox("Escenario", ["A", "B", "Compare A vs B"])
    cfg["duration_min"] = st.sidebar.number_input("Duración (min)", value=defaults.get("duration_min", 60))
    cfg["run_mode"] = st.sidebar.selectbox("Modo de ejecución", ["Live", "Weekly Compare"])
    return cfg


def estimate_costs(cfg: Dict, summary: Dict, scenario: str) -> Dict:
    # Reuse same estimation as scripts
    hours = 7 * 24
    forklift_hours = hours if scenario == "A" else 0
    num_forklifts = cfg.get("num_forklifts", 1)
    labor_cost = cfg.get("forklift_operator_cost", 35.0) * num_forklifts * forklift_hours
    maint_forklift_week = cfg.get("maintenance_cost_forklift", 12000) / 52.0
    maint_ingetrans_week = cfg.get("maintenance_cost_ingetrans", 4000) / 52.0
    maintenance = maint_forklift_week if scenario == "A" else maint_ingetrans_week
    starvation_cost = cfg.get("cost_per_starvation_event", 150.0) * summary.get("starvation_count", 0)
    downtime_min = summary.get("starvation_count", 0) * 5
    downtime_cost = downtime_min * cfg.get("cost_of_corrugator_downtime", 45.0)
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


def run_weekly_compare(cfg: Dict):
    duration_min = 7 * 24 * 60
    results = {}
    for scenario in ("A", "B"):
        eng = CorrugatorEngineV3(config=cfg, scenario=scenario, seed=123)
        steps = int(duration_min)
        sample_every = 60
        samples = []
        for i in range(steps):
            eng.step(1.0)
            if (i + 1) % sample_every == 0:
                samples.append(calculate_kpis(eng))
        total = eng.metrics.get("production_meters", 0.0)
        results[scenario] = {
            "total_production_m": total,
            "starvation_count": eng.metrics.get("starvation_count", 0),
            "deliveries_scheduled": eng.metrics.get("deliveries_scheduled", 0),
            "deliveries_successful": eng.metrics.get("deliveries_successful", 0),
            "avg_kpis": {k: (sum(s[k] for s in samples) / max(len(samples), 1)) for k in samples[0].keys()} if samples else {},
        }
    return results


def main():
    defaults = load_defaults()
    cfg = sidebar_config(defaults)

    st.title("Reel Load Simulator — Commercial Demo v3")

    left, right = st.columns([2, 1])
    svg_placeholder = left.empty()
    kpi_box = right.empty()

    if cfg["run_mode"] == "Live":
        if st.button("Ejecutar simulación en vivo"):
            scenario = cfg.get("scenario_select", "B")
            engine = CorrugatorEngineV3(config={**defaults, **cfg}, scenario=scenario)
            steps = int(cfg.get("duration_min", 60))
            flow_p = left.empty()
            sat_p = left.empty()
            oee_p = left.empty()
            with st.spinner("Simulando..."):
                for i in range(steps):
                    engine.step(1.0)
                    kpis = calculate_kpis(engine)
                    state_counts = {}
                    for t in engine.tracks:
                        state_counts.setdefault(t["state"].name, 0)
                        state_counts[t["state"].name] += 1
                    svg = render_plant_svg(engine)
                    svg_placeholder.markdown(svg, unsafe_allow_html=True)
                    flow_fig = flow_chart(state_counts)
                    sat_fig = saturation_chart({
                        "Transfer": min(100.0, 10.0 + kpis["LPI"]),
                        "Forklift": 50.0,
                        "Tracks": kpis["track_saturation"],
                        "Buffer": 30.0,
                    })
                    oee_fig = oee_chart({f"Stand {s.id+1}": kpis["OEE"] for s in engine.roll_stands})
                    # Use explicit plotly_chart calls with unique keys to avoid
                    # StreamlitDuplicateElementId when re-rendering in a loop.
                    flow_p.plotly_chart(flow_fig, use_container_width=True, key=f"flow_plot_{scenario}_{i}")
                    sat_p.plotly_chart(sat_fig, use_container_width=True, key=f"sat_plot_{scenario}_{i}")
                    oee_p.plotly_chart(oee_fig, use_container_width=True, key=f"oee_plot_{scenario}_{i}")
                    kpi_box.metric("LPI", f"{kpis['LPI']:.1f}")
                    kpi_box.metric("RRI", f"{kpis['RRI']:.2f}")
                    kpi_box.metric("PSS", f"{kpis['PSS']:.1f}%")
                    kpi_box.metric("OEE", f"{kpis['OEE']:.1f}%")
                    time.sleep(0.01)

    else:
        if st.button("Run Weekly Compare (A vs B)"):
            with st.spinner("Ejecutando comparativa semanal..."):
                results = run_weekly_compare({**defaults, **cfg})
                costsA = estimate_costs({**defaults, **cfg}, results["A"], "A")
                costsB = estimate_costs({**defaults, **cfg}, results["B"], "B")
                prodA = results["A"]["total_production_m"]
                prodB = results["B"]["total_production_m"]
                diff = prodB - prodA
                costdiff = costsB["total_operational_cost_week"] - costsA["total_operational_cost_week"]
                out = {
                    "results": results,
                    "costsA": costsA,
                    "costsB": costsB,
                    "comparison": {"prod_diff_m": diff, "cost_diff_eur": costdiff},
                }
                st.success("Comparativa completada")
                st.write("### Resumen semanal")
                st.write(f"Producción A: {prodA:,.1f} m — Producción B: {prodB:,.1f} m — Diff: {diff:,.1f} m")
                st.write(f"Coste semanal A: {costsA['total_operational_cost_week']:.2f} € — B: {costsB['total_operational_cost_week']:.2f} € — Diff: {costdiff:.2f} €")
                st.download_button("Descargar JSON de resultados", data=json.dumps(out, indent=2), file_name="weekly_compare_results.json")


if __name__ == "__main__":
    main()
