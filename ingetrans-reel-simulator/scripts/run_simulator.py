#!/usr/bin/env python3
"""Minimal simulator runner for Reel Loading Simulator V4.

This toy runner reads configs and a scenario YAML and performs a simple
discrete-time simulation that generates 'completed production orders' as events.
It writes outputs to `ingetrans-reel-simulator/outputs/<run_id>/`.
"""

import argparse
import os
import time
import yaml
import random
import json
import csv
from datetime import datetime


def nested_get_with_default(d, *keys):
    v = d
    for k in keys:
        if not isinstance(v, dict) or k not in v:
            return None
        v = v[k]
    if isinstance(v, dict) and 'default' in v:
        return v['default']
    return v


def load_config_db(root_dir):
    cfg_dir = os.path.join(root_dir, '03_CONFIG_DATABASE')
    configs = {}
    for fn in os.listdir(cfg_dir):
        if fn.lower().endswith(('.yml', '.yaml')):
            path = os.path.join(cfg_dir, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    configs[fn] = yaml.safe_load(f)
            except Exception:
                configs[fn] = None
    return configs


def run_simulation(root_dir, scenario_path, run_duration_s=None, tick_s=None, seed=42):
    random.seed(seed)
    configs = load_config_db(root_dir)

    # Load scenario
    with open(scenario_path, 'r', encoding='utf-8') as f:
        scenario = yaml.safe_load(f) or {}

    # Resolve tick
    if tick_s is None:
        sim_clock = configs.get('config_simulation_clock.yaml', {})
        tick_s = nested_get_with_default(sim_clock, 'parameters', 0, 'default') if isinstance(sim_clock, dict) else None
        # fallback to parameter structure used in config_simulation_clock.yaml
        if tick_s is None:
            # try reading the documented `tick_s` default
            tick_s = 1.0

    # Resolve run duration
    if run_duration_s is None:
        run_duration_s = nested_get_with_default(scenario, 'run_duration_s') or 3600

    # Resolve production order interarrival (mean seconds)
    prod_interarrival = nested_get_with_default(scenario, 'production_order', 'interarrival_min_s')
    if prod_interarrival is None:
        # try to read from scenario where value is nested under default
        prod_interarrival = nested_get_with_default(scenario, 'production_order', 'interarrival_min_s')
    if prod_interarrival is None:
        # fallback to a reasonable default
        prod_interarrival = 600.0

    try:
        prod_interarrival = float(prod_interarrival)
    except Exception:
        prod_interarrival = 600.0

    # Prepare run outputs
    run_id = datetime.utcnow().strftime('run_%Y%m%dT%H%M%SZ')
    out_dir = os.path.join(root_dir, 'outputs', run_id)
    os.makedirs(out_dir, exist_ok=True)

    events = []
    completed_orders = 0

    # schedule first order
    if prod_interarrival > 0:
        next_order_time = random.expovariate(1.0 / prod_interarrival)
    else:
        next_order_time = float('inf')

    t = 0.0
    steps = 0
    start_ts = datetime.utcnow().isoformat() + 'Z'

    while t < run_duration_s:
        # handle arrivals
        while t >= next_order_time:
            completed_orders += 1
            ev = {
                'timestamp': t,
                'entity_type': 'ProductionOrder',
                'entity_id': str(completed_orders),
                'type': 'completed',
                'payload': {}
            }
            events.append(ev)
            # schedule next
            next_order_time += random.expovariate(1.0 / prod_interarrival)

        # emit tick event (sampled)
        if steps % int(max(1, round(1.0 / tick_s))) == 0:
            events.append({'timestamp': t, 'entity_type': 'SimulationClock', 'entity_id': '', 'type': 'tick', 'payload': {'tick_s': tick_s}})

        t += tick_s
        steps += 1

    end_ts = datetime.utcnow().isoformat() + 'Z'

    duration_hours = max(1e-9, run_duration_s / 3600.0)
    throughput_rph = completed_orders / duration_hours

    # write run summary
    summary = {
        'run_id': run_id,
        'scenario': os.path.basename(scenario_path),
        'start_ts': start_ts,
        'end_ts': end_ts,
        'run_duration_s': run_duration_s,
        'tick_s': tick_s,
        'completed_orders': completed_orders,
        'throughput_rolls_per_hour': throughput_rph
    }

    with open(os.path.join(out_dir, 'run_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    # write event log CSV
    csv_path = os.path.join(out_dir, 'event_log.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as cf:
        writer = csv.writer(cf)
        writer.writerow(['timestamp', 'entity_type', 'entity_id', 'event_type', 'payload'])
        for e in events:
            writer.writerow([e['timestamp'], e['entity_type'], e['entity_id'], e['type'], json.dumps(e.get('payload', {}))])

    print('Run finished:', run_id)
    print('Summary:')
    print(json.dumps(summary, indent=2))
    print('Outputs written to:', out_dir)


def main():
    parser = argparse.ArgumentParser(description='Run minimal Reel Loading Simulator V4')
    parser.add_argument('--scenario', '-s', help='Scenario YAML file', default=os.path.join(os.path.dirname(os.path.dirname(__file__)), '06_SCENARIOS', 'scenario_01_baseline_forklift.yaml'))
    parser.add_argument('--duration', '-d', type=float, help='Run duration in seconds', default=None)
    parser.add_argument('--tick', '-t', type=float, help='Tick seconds override', default=None)
    parser.add_argument('--seed', type=int, default=42)

    args = parser.parse_args()
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    run_simulation(root_dir, args.scenario, run_duration_s=args.duration, tick_s=args.tick, seed=args.seed)


if __name__ == '__main__':
    main()
