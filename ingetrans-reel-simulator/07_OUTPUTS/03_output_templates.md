# Output Templates

Plantillas de salida sugeridas:

- `run_summary.csv`:
  - columns: run_id, scenario_id, start_time, end_time, duration_s, throughput, oee, total_scrap_kg

- `event_log.csv`:
  - columns: timestamp, entity_type, entity_id, event_type, payload_json

- `inventory_timeseries.csv`:
  - columns: timestamp, reel_id, location, remaining_m, mass_kg
