-- Schema for Competitive Intelligence SQLite store (scaffold)

CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE,
  seed_url TEXT,
  meta TEXT
);

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY,
  company_id INTEGER,
  url TEXT,
  type TEXT,
  discovered_at REAL
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY,
  company_id INTEGER,
  source_id INTEGER,
  file_name TEXT,
  file_path TEXT,
  url TEXT,
  last_modified REAL,
  content TEXT,
  summary TEXT,
  status TEXT,
  version INTEGER,
  meta TEXT
);

CREATE TABLE IF NOT EXISTS entities (
  id INTEGER PRIMARY KEY,
  doc_id INTEGER,
  type TEXT,
  text TEXT,
  canonical_id TEXT,
  meta TEXT
);

CREATE TABLE IF NOT EXISTS kg_edges (
  id INTEGER PRIMARY KEY,
  from_id TEXT,
  relation TEXT,
  to_id TEXT,
  weight REAL,
  evidence_doc INTEGER
);
