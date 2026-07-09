"""
Lightweight persistence and import utilities for Project Closeout.
This module provides a minimal SQLite-backed service to store projects,
documents, issues and related metadata used by the Streamlit UI.
"""
from __future__ import annotations

import csv
import io
import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def compute_sha256(path: str, block_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()


class ProjectCloseoutService:
    def __init__(self, db_path: Optional[str] = None):
        root = os.path.join("data", "project_closeout")
        _ensure_dir(root)
        self.db_path = db_path or os.path.join(root, "closeout.db")
        _ensure_dir(os.path.dirname(self.db_path))
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_tables()

    def _ensure_tables(self):
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                project_id TEXT UNIQUE,
                project_name TEXT,
                master_data TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                project_id TEXT,
                path TEXT,
                filename TEXT,
                doc_type TEXT,
                size INTEGER,
                file_hash TEXT,
                extracted TEXT,
                inserted_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY,
                project_id TEXT,
                issue_id TEXT,
                source TEXT,
                category TEXT,
                description TEXT,
                priority TEXT,
                date_opened TEXT,
                owner TEXT,
                due_date TEXT,
                status TEXT,
                resolution_date TEXT,
                root_cause TEXT,
                corrective_action TEXT,
                preventive_action TEXT,
                linked_document TEXT,
                notes TEXT,
                inserted_at TEXT,
                updated_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS change_orders (
                id INTEGER PRIMARY KEY,
                project_id TEXT,
                change_id TEXT,
                date TEXT,
                title TEXT,
                description TEXT,
                origin TEXT,
                commercial_impact REAL,
                schedule_impact_days INTEGER,
                approved INTEGER DEFAULT 0,
                approval_date TEXT,
                notes TEXT,
                inserted_at TEXT
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS report_versions (
                id INTEGER PRIMARY KEY,
                project_id TEXT,
                version TEXT,
                path_html TEXT,
                path_json TEXT,
                generated_at TEXT
            )
            """
        )

        self._conn.commit()

    # ---------------------- Projects ---------------------------------
    def list_projects(self) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT project_id, project_name, master_data, updated_at FROM projects ORDER BY updated_at DESC")
        rows = cur.fetchall()
        out = []
        for r in rows:
            md = None
            try:
                md = json.loads(r["master_data"]) if r["master_data"] else {}
            except Exception:
                md = {}
            out.append({"project_id": r["project_id"], "project_name": r["project_name"], "master_data": md, "updated_at": r["updated_at"]})
        return out

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
        r = cur.fetchone()
        if not r:
            return None
        try:
            master_data = json.loads(r["master_data"]) if r["master_data"] else {}
        except Exception:
            master_data = {}
        return {"project_id": r["project_id"], "project_name": r["project_name"], "master_data": master_data, "created_at": r["created_at"], "updated_at": r["updated_at"]}

    def upsert_project(self, project_id: str, payload: Dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        cur = self._conn.cursor()
        # project_name promoted if present
        project_name = payload.get("project_name") or payload.get("name") or project_id
        master_json = json.dumps(payload, ensure_ascii=False)
        cur.execute(
            "INSERT OR REPLACE INTO projects (id, project_id, project_name, master_data, created_at, updated_at) VALUES ((SELECT id FROM projects WHERE project_id=?), ?, ?, ?, COALESCE((SELECT created_at FROM projects WHERE project_id=?), ?), ?)",
            (project_id, project_id, project_name, master_json, project_id, now, now),
        )
        self._conn.commit()

    # ---------------------- Documents --------------------------------
    def save_document(self, project_id: str, uploaded_file, doc_type: str = "generic") -> Dict[str, Any]:
        root = os.path.join("data", "project_closeout", "files", project_id)
        _ensure_dir(root)
        filename = getattr(uploaded_file, "name", None) or f"upload_{uuid.uuid4().hex}"
        safe_name = filename.replace(" ", "_")
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        target = os.path.join(root, f"{timestamp}_{safe_name}")
        # uploaded_file may be BytesIO or similar
        data = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
        with open(target, "wb") as f:
            f.write(data)
        size = os.path.getsize(target)
        file_hash = compute_sha256(target)
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO documents (project_id, path, filename, doc_type, size, file_hash, extracted, inserted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, os.path.relpath(target), filename, doc_type, size, file_hash, None, datetime.utcnow().isoformat() + "Z"),
        )
        self._conn.commit()
        return {"path": target, "filename": filename, "size": size, "file_hash": file_hash}

    # ---------------------- Issues / Punch list -----------------------
    def import_issues_from_file(self, project_id: str, file_stream, filename: str) -> Dict[str, Any]:
        """Attempt to parse CSV/XLSX/TSV-ish punch lists and insert them into `issues` table.

        Returns a summary dict with inserted count and any rows flagged for review.
        """
        inserted = 0
        rows_for_review = []
        # Try pandas first for convenience
        try:
            import pandas as pd

            if filename.lower().endswith(".xlsx") or filename.lower().endswith(".xls"):
                df = pd.read_excel(file_stream)
            else:
                # assume csv / delim
                try:
                    df = pd.read_csv(file_stream)
                except Exception:
                    # try with semicolon
                    file_stream.seek(0)
                    df = pd.read_csv(file_stream, sep=";")

            # normalize column names
            df_cols = {c.lower().strip(): c for c in df.columns}
            def _map(col_candidates):
                for c in col_candidates:
                    if c in df_cols:
                        return df_cols[c]
                return None

            id_col = _map(["issue id", "id", "issue_id", "issueid"]) or None
            desc_col = _map(["description", "desc", "detalle", "comment"]) or None
            owner_col = _map(["owner", "responsible", "assignee"]) or None
            status_col = _map(["status", "estado"]) or None
            priority_col = _map(["priority", "prioridad"]) or None
            date_col = _map(["date", "date opened", "date_opened", "fecha"]) or None

            cur = self._conn.cursor()
            for _, row in df.iterrows():
                issue_id = str(row[id_col]) if id_col and not pd.isna(row[id_col]) else f"ISS-{uuid.uuid4().hex[:8]}"
                description = str(row[desc_col]) if desc_col and not pd.isna(row[desc_col]) else ""
                owner = str(row[owner_col]) if owner_col and not pd.isna(row[owner_col]) else None
                status = str(row[status_col]) if status_col and not pd.isna(row[status_col]) else "Open"
                priority = str(row[priority_col]) if priority_col and not pd.isna(row[priority_col]) else "Medium"
                date_opened = str(row[date_col]) if date_col and not pd.isna(row[date_col]) else None
                cur.execute(
                    "INSERT INTO issues (project_id, issue_id, source, category, description, priority, date_opened, owner, status, inserted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        project_id,
                        issue_id,
                        "import",
                        None,
                        description,
                        priority,
                        date_opened,
                        owner,
                        status,
                        datetime.utcnow().isoformat() + "Z",
                    ),
                )
                inserted += 1
            self._conn.commit()
            return {"inserted": inserted, "rows_for_review": rows_for_review}
        except Exception:
            # fallback: simple CSV reader
            try:
                file_stream.seek(0)
                reader = csv.DictReader(io.TextIOWrapper(file_stream, encoding="utf-8"))
                cur = self._conn.cursor()
                for row in reader:
                    issue_id = row.get("Issue ID") or row.get("id") or f"ISS-{uuid.uuid4().hex[:8]}"
                    description = row.get("Description") or row.get("description") or ""
                    owner = row.get("Owner") or None
                    status = row.get("Status") or "Open"
                    priority = row.get("Priority") or "Medium"
                    cur.execute(
                        "INSERT INTO issues (project_id, issue_id, source, category, description, priority, date_opened, owner, status, inserted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (project_id, issue_id, "import", None, description, priority, None, owner, status, datetime.utcnow().isoformat() + "Z"),
                    )
                    inserted += 1
                self._conn.commit()
                return {"inserted": inserted, "rows_for_review": rows_for_review}
            except Exception as exc:
                return {"error": str(exc)}

    def list_issues(self, project_id: str) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM issues WHERE project_id = ? ORDER BY inserted_at DESC", (project_id,))
        return [dict(r) for r in cur.fetchall()]

    def get_issues_df(self, project_id: str):
        # Return a pandas DataFrame when possible
        try:
            import pandas as pd

            rows = self.list_issues(project_id)
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame(rows)
        except Exception:
            return self.list_issues(project_id)

    # ---------------------- Change orders -----------------------------
    def add_change_order(self, project_id: str, payload: Dict[str, Any]) -> None:
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO change_orders (project_id, change_id, date, title, description, origin, commercial_impact, schedule_impact_days, approved, approval_date, notes, inserted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                project_id,
                payload.get("change_id") or f"CO-{uuid.uuid4().hex[:8]}",
                payload.get("date"),
                payload.get("title"),
                payload.get("description"),
                payload.get("origin"),
                payload.get("commercial_impact"),
                payload.get("schedule_impact_days"),
                1 if payload.get("approved") else 0,
                payload.get("approval_date"),
                payload.get("notes"),
                datetime.utcnow().isoformat() + "Z",
            ),
        )
        self._conn.commit()

    def list_change_orders(self, project_id: str) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM change_orders WHERE project_id = ? ORDER BY inserted_at DESC", (project_id,))
        return [dict(r) for r in cur.fetchall()]
