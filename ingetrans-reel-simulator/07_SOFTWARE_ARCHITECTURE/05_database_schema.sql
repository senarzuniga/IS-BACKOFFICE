-- 05_database_schema.sql
-- Esquema SQL mínimo para persistencia de runs, events, kpis y configs

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  scenario_id TEXT,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  status TEXT,
  metadata JSON
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  run_id TEXT REFERENCES runs(id),
  timestamp TIMESTAMP,
  entity_type TEXT,
  entity_id TEXT,
  type TEXT,
  payload JSON
);

CREATE TABLE IF NOT EXISTS kpi_snapshots (
  id TEXT PRIMARY KEY,
  run_id TEXT REFERENCES runs(id),
  timestamp TIMESTAMP,
  kpis JSON
);

CREATE TABLE IF NOT EXISTS configs (
  id TEXT PRIMARY KEY,
  name TEXT,
  content YAML
);
