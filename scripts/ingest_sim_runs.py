#!/usr/bin/env python3
"""Simple ingestion tool for simulator runs.

Scans `ingetrans-reel-simulator/outputs/*` for `run_summary.json` and `event_log.csv`,
and writes a small SQLite 'superbase' with run metadata and optional events.

Usage:
  python scripts/ingest_sim_runs.py [--db data/sim_runs/superbase.db] [--outputs ingetrans-reel-simulator/outputs] [--store-events] [--dry-run]
"""
import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime


def compute_sha256(path, block_size=65536):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


def ensure_db(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY,
            run_id TEXT UNIQUE,
            scenario TEXT,
            start_ts TEXT,
            end_ts TEXT,
            run_duration_s REAL,
            tick_s REAL,
            completed_orders INTEGER,
            throughput_rolls_per_hour REAL,
            path TEXT,
            file_size_bytes INTEGER,
            file_hash TEXT,
            ingested_at TEXT,
            useful INTEGER DEFAULT 0,
            notes TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            run_id TEXT,
            timestamp REAL,
            entity_type TEXT,
            entity_id TEXT,
            event_type TEXT,
            payload TEXT
        )
        """
    )
    conn.commit()


def ingest_run(output_dir, db_conn, store_events=False, dry_run=False):
    run_summary_path = os.path.join(output_dir, "run_summary.json")
    event_log_path = os.path.join(output_dir, "event_log.csv")
    if not os.path.exists(run_summary_path):
        print(f"Skipping {output_dir}: no run_summary.json")
        return None

    with open(run_summary_path, "r", encoding="utf-8") as f:
        run_summary = json.load(f)

    file_size = os.path.getsize(event_log_path) if os.path.exists(event_log_path) else 0
    file_hash = compute_sha256(event_log_path) if os.path.exists(event_log_path) else None

    # derive basic analytics from event_log.csv
    event_counts = 0
    event_type_counts = {}
    entity_type_counts = {}
    sample_events = []

    if os.path.exists(event_log_path):
        with open(event_log_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                event_counts += 1
                et = row.get('event_type')
                entity = row.get('entity_type')
                event_type_counts[et] = event_type_counts.get(et, 0) + 1
                entity_type_counts[entity] = entity_type_counts.get(entity, 0) + 1
                if i < 10:
                    payload = row.get('payload')
                    parsed_payload = None
                    if payload:
                        try:
                            parsed_payload = json.loads(payload)
                        except Exception:
                            # fallback: replace doubled quotes produced by CSV escaping
                            try:
                                parsed_payload = json.loads(payload.replace('""', '"'))
                            except Exception:
                                parsed_payload = payload
                    sample_events.append({
                        'timestamp': float(row.get('timestamp') or 0.0),
                        'entity_type': entity,
                        'event_type': et,
                        'payload': parsed_payload,
                    })

    # simple usefulness heuristic
    useful = 1 if event_counts > 0 and any(k != 'tick' for k in event_type_counts.keys()) else 0

    if dry_run:
        print(json.dumps({
            'run_id': run_summary.get('run_id'),
            'file_size': file_size,
            'event_counts': event_counts,
            'event_type_counts': event_type_counts,
            'entity_type_counts': entity_type_counts,
            'useful': useful,
            'sample_events': sample_events,
        }, indent=2, default=str))
        return None

    cur = db_conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO runs (run_id, scenario, start_ts, end_ts, run_duration_s, tick_s, completed_orders, throughput_rolls_per_hour, path, file_size_bytes, file_hash, ingested_at, useful, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_summary.get('run_id'),
            run_summary.get('scenario'),
            run_summary.get('start_ts'),
            run_summary.get('end_ts'),
            run_summary.get('run_duration_s'),
            run_summary.get('tick_s'),
            run_summary.get('completed_orders'),
            run_summary.get('throughput_rolls_per_hour'),
            os.path.relpath(output_dir),
            file_size,
            file_hash,
            datetime.utcnow().isoformat() + 'Z',
            useful,
            None,
        ),
    )

    if store_events and os.path.exists(event_log_path):
        with open(event_log_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            to_insert = []
            for row in reader:
                payload = row.get('payload')
                parsed_payload = None
                if payload:
                    try:
                        parsed_payload = json.loads(payload)
                    except Exception:
                        try:
                            parsed_payload = json.loads(payload.replace('""', '"'))
                        except Exception:
                            parsed_payload = payload
                to_insert.append((
                    run_summary.get('run_id'),
                    float(row.get('timestamp') or 0.0),
                    row.get('entity_type'),
                    row.get('entity_id'),
                    row.get('event_type'),
                    json.dumps(parsed_payload, ensure_ascii=False) if parsed_payload is not None else None,
                ))
            cur.executemany(
                "INSERT INTO events (run_id, timestamp, entity_type, entity_id, event_type, payload) VALUES (?, ?, ?, ?, ?, ?)",
                to_insert,
            )

    db_conn.commit()
    print(f"Ingested run {run_summary.get('run_id')} (events: {event_counts})")
    return run_summary.get('run_id')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='data/sim_runs/superbase.db')
    parser.add_argument('--outputs', default='ingetrans-reel-simulator/outputs')
    parser.add_argument('--store-events', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.db), exist_ok=True)
    conn = sqlite3.connect(args.db)
    ensure_db(conn)

    outputs_root = args.outputs
    if not os.path.exists(outputs_root):
        print(f"Outputs root not found: {outputs_root}")
        sys.exit(1)

    subdirs = sorted([os.path.join(outputs_root, d) for d in os.listdir(outputs_root) if os.path.isdir(os.path.join(outputs_root, d))])
    if not subdirs:
        print("No runs found under outputs root.")
        sys.exit(0)

    for d in subdirs:
        ingest_run(d, conn, store_events=args.store_events, dry_run=args.dry_run)

    conn.close()


if __name__ == '__main__':
    main()
