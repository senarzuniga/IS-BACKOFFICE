PROJECT DATABASE SCHEMA V2

Overview and recommendations
----------------------------
Use a robust relational DB (Postgres recommended) for canonical project data. For local/dev, keep SQLite compatibility adapters to support existing files (`data/project_closeout/closeout.db`). Use an object store for binaries and a vector store (Chroma/FAISS) for embeddings.

Guiding principles
- `canonical_project_id` as the primary business key (unique across systems).
- Use `UUID` PKs and a human-friendly `canonical_project_id` as secondary unique identifier.
- Partition and index by `canonical_project_id` to keep queries efficient.
- Store flexible metadata in `jsonb` columns for rapid iteration.

DDL (Postgres flavour) — core tables
-----------------------------------
-- Projects
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_project_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  code TEXT,
  status TEXT,
  customer_id TEXT,
  start_date DATE,
  end_date DATE,
  budget NUMERIC,
  currency TEXT,
  external_ids JSONB,
  metadata JSONB,
  source TEXT,
  source_id TEXT,
  confidence REAL DEFAULT 1.0,
  truth_status TEXT DEFAULT 'unverified',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  created_by TEXT,
  updated_by TEXT
);
CREATE INDEX idx_projects_customer ON projects(customer_id);
CREATE INDEX idx_projects_canonical ON projects(canonical_project_id);

-- Project phases
CREATE TABLE project_phases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  name TEXT,
  phase_order INTEGER,
  start_date DATE,
  end_date DATE,
  metadata JSONB
);

-- Milestones
CREATE TABLE milestones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  phase_id UUID REFERENCES project_phases(id) ON DELETE SET NULL,
  name TEXT,
  planned_date DATE,
  actual_date DATE,
  critical BOOLEAN DEFAULT FALSE,
  status TEXT
);

-- Tasks
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  phase_id UUID REFERENCES project_phases(id) ON DELETE SET NULL,
  milestone_id UUID REFERENCES milestones(id) ON DELETE SET NULL,
  title TEXT,
  description TEXT,
  assignee_id TEXT,
  estimated_hours NUMERIC,
  actual_hours NUMERIC,
  start_date DATE,
  end_date DATE,
  status TEXT,
  dependencies UUID[],
  priority TEXT,
  metadata JSONB
);
CREATE INDEX idx_tasks_project ON tasks(project_id);

-- Risks
CREATE TABLE risks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT,
  description TEXT,
  probability TEXT,
  impact TEXT,
  mitigation TEXT,
  owner_id TEXT,
  status TEXT,
  risk_score NUMERIC,
  metadata JSONB
);

-- Issues (punchlist)
CREATE TABLE issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  issue_key TEXT,
  source TEXT,
  category TEXT,
  description TEXT,
  priority TEXT,
  date_opened TIMESTAMPTZ,
  owner_id TEXT,
  due_date DATE,
  status TEXT,
  resolution TEXT,
  linked_document_ids UUID[],
  metadata JSONB,
  inserted_at TIMESTAMPTZ DEFAULT now()
);

-- Decisions & Actions
CREATE TABLE decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT,
  date TIMESTAMPTZ,
  text TEXT,
  decided_by TEXT,
  approval_status TEXT,
  metadata JSONB
);

CREATE TABLE actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT,
  assigned_to TEXT,
  due_date DATE,
  status TEXT,
  related_decision_id UUID REFERENCES decisions(id),
  metadata JSONB
);

-- Meetings
CREATE TABLE meetings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT,
  meeting_date TIMESTAMPTZ,
  participants TEXT[],
  minutes_document_id UUID,
  action_item_ids UUID[],
  metadata JSONB
);

-- Documents
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  filename TEXT,
  doc_type TEXT,
  object_store_url TEXT,
  path TEXT,
  size BIGINT,
  file_hash TEXT,
  extracted_text TEXT,
  extracted_entities JSONB,
  confidence REAL,
  source TEXT,
  source_id TEXT,
  uploaded_at TIMESTAMPTZ DEFAULT now(),
  uploaded_by TEXT,
  metadata JSONB
);
CREATE INDEX idx_documents_project ON documents(project_id);

-- Document versions (revision control)
CREATE TABLE document_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  version_label TEXT,
  object_store_url TEXT,
  file_hash TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  created_by TEXT
);

-- ERP references (lightweight mapping)
CREATE TABLE external_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  system TEXT,
  external_id TEXT,
  metadata JSONB
);

-- Truth Graph (node / edge pattern)
CREATE TABLE graph_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  node_type TEXT,
  project_id UUID,
  payload JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE graph_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_node_id UUID REFERENCES graph_nodes(id) ON DELETE CASCADE,
  target_node_id UUID REFERENCES graph_nodes(id) ON DELETE CASCADE,
  relation_type TEXT,
  confidence REAL,
  metadata JSONB
);

Notes on ERP integration and financial tables
-------------------------------------------
- Rather than duplicating invoices / POs, store mappings in `external_mappings` and optionally materialize financial snapshots in `invoices`/`payments` tables if reconciliation or reporting performance requires it.

Sample view: project_financial_summary
CREATE VIEW project_financial_summary AS
SELECT p.canonical_project_id, p.name,
  SUM(i.total) FILTER (WHERE i.status <> 'cancelled') AS invoiced,
  SUM(pay.amount) AS paid,
  (SUM(i.total) - SUM(pay.amount)) AS outstanding
FROM projects p
LEFT JOIN invoices i ON i.project_id = p.id
LEFT JOIN payments pay ON pay.invoice_id = i.id
GROUP BY p.canonical_project_id, p.name;

Migration strategy (from existing closeout.db + ERP)
---------------------------------------------------
1. Provision Postgres schema and keep SQLite for developer convenience.
2. Create `projects` entries by reading `data/project_closeout/closeout.db` projects table and creating canonical entries with `external_ids.closeout` set.
3. Run ERP adapter in read-only mode to map ERP project rows into `external_mappings` and create canonical entries where missing.
4. Update Closeout local DB rows to include `canonical_project_id` (or keep mapping table). During cut-over applications read both until fully migrated.

Indexes & performance
---------------------
- Index `project_id` references on large tables (documents, tasks, issues).
- Use partial indexes for open issues, active tasks.
- Consider sharding/partitioning by project_id for extremely large projects.

Storage & object store
----------------------
- Store binaries in S3-compatible object store. Keep `object_store_url` and `file_hash` in DB. Use signed URLs for downloads.

Vector store & Knowledge Memory
------------------------------
- Store embeddings in Chroma/VectorDB. Save mapping metadata with `document_id` and `project_id`.

Testing & validation
--------------------
- Unit tests for DDL migrations and adapters.
- Integration tests: create canonical project, ingest document, assert Knowledge Hub index contains project id.
