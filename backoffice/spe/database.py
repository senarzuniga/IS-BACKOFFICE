"""Service Proposal Engine — resilient SQLite database layer."""
from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .models import MissionEntry, Proposal, ProposalVersion, ServiceItem


_LOCK = threading.Lock()
_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "spe_proposals.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _seq_from_number(number: str, year: int) -> int:
    match = re.fullmatch(rf"OFF-{year}-S(\d+)", (number or "").strip())
    if not match:
        return -1
    return int(match.group(1))


class SQLiteConnectionManager:
    """Centralized SQLite connection manager with health and recovery helpers."""

    def __init__(self, db_path: Path, busy_timeout_ms: int = 6000, retries: int = 5) -> None:
        self.db_path = db_path
        self.busy_timeout_ms = busy_timeout_ms
        self.retries = retries

    @contextmanager
    def connect(self, write: bool = False) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=max(1, self.busy_timeout_ms // 1000))
            conn.row_factory = sqlite3.Row
            conn.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms};")
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            if write:
                conn.commit()
        except sqlite3.OperationalError as exc:
            if conn is not None:
                conn.rollback()
            msg = str(exc).lower()
            if "readonly" in msg:
                raise sqlite3.OperationalError(
                    f"readonly database root cause: db={self.db_path} parent_writable={os.access(self.db_path.parent, os.W_OK)}"
                ) from exc
            raise
        finally:
            if conn is not None:
                conn.close()

    def backup(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.db_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / f"spe_proposals_{ts}.db"
        if self.db_path.exists():
            shutil.copy2(self.db_path, target)
        return str(target)

    def health_report(self) -> dict[str, Any]:
        report: dict[str, Any] = {
            "db_path": str(self.db_path),
            "exists": self.db_path.exists(),
            "path_ok": True,
            "permissions": {
                "read": os.access(self.db_path.parent, os.R_OK),
                "write": os.access(self.db_path.parent, os.W_OK),
            },
            "root_causes": [],
            "sqlite": {},
            "status": "PASS",
        }
        if not report["permissions"]["write"]:
            report["root_causes"].append("Directory not writable")
        if not self.db_path.exists():
            report["root_causes"].append("Database file not found")

        try:
            with self.connect(write=False) as conn:
                quick = conn.execute("PRAGMA quick_check;").fetchone()[0]
                integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
                journal = conn.execute("PRAGMA journal_mode;").fetchone()[0]
                fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
                busy = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
                report["sqlite"] = {
                    "quick_check": quick,
                    "integrity_check": integrity,
                    "journal_mode": journal,
                    "foreign_keys": bool(fk),
                    "busy_timeout": busy,
                }
                if str(quick).lower() != "ok":
                    report["root_causes"].append(f"quick_check={quick}")
                if str(integrity).lower() != "ok":
                    report["root_causes"].append(f"integrity_check={integrity}")
                if str(journal).lower() != "wal":
                    report["root_causes"].append(f"journal_mode={journal}")
                if not bool(fk):
                    report["root_causes"].append("foreign_keys disabled")
        except Exception as exc:
            report["root_causes"].append(str(exc))

        if report["root_causes"]:
            report["status"] = "FAIL"
        return report


class SPEDatabase:
    """Persistent storage for Service Proposal Engine proposals."""

    def __init__(self, db_path: Path = _DB_PATH):
        self.db_path = db_path
        self.conn_manager = SQLiteConnectionManager(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        if self.db_path.exists():
            self.conn_manager.backup()
        with self.conn_manager.connect(write=True) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS proposals (
                    id               TEXT PRIMARY KEY,
                    number           TEXT UNIQUE,
                    title            TEXT,
                    status           TEXT DEFAULT 'draft',
                    version          INTEGER DEFAULT 1,
                    customer         TEXT,
                    customer_contact TEXT,
                    customer_email   TEXT,
                    customer_phone   TEXT,
                    customer_address TEXT,
                    customer_country TEXT,
                    plant            TEXT,
                    language         TEXT DEFAULT 'en',
                    currency         TEXT DEFAULT 'EUR',
                    responsible      TEXT DEFAULT 'INGECART',
                    commercial       TEXT,
                    project          TEXT,
                    duration         TEXT,
                    validity_days    INTEGER DEFAULT 30,
                    incoterm         TEXT,
                    payment_terms    TEXT,
                    observations     TEXT,
                    date_created     TEXT,
                    date_sent        TEXT,
                    date_accepted    TEXT,
                    date_expiry      TEXT,
                    services_json    TEXT DEFAULT '[]',
                    executive_summary TEXT DEFAULT '',
                    about_ingecart   TEXT DEFAULT '',
                    understanding_installation TEXT DEFAULT '',
                    objectives       TEXT DEFAULT '',
                    scope_of_services TEXT DEFAULT '',
                    maintenance_programme TEXT DEFAULT '',
                    visit_methodology TEXT DEFAULT '',
                    deliverables     TEXT DEFAULT '',
                    ingpro_section   TEXT DEFAULT '',
                    optional_services TEXT DEFAULT '',
                    customer_responsibilities TEXT DEFAULT '',
                    commercial_conditions TEXT DEFAULT '',
                    pricing_summary  TEXT DEFAULT '',
                    why_ingecart     TEXT DEFAULT '',
                    acceptance       TEXT DEFAULT '',
                    annexes          TEXT DEFAULT '',
                    ai_comments_json TEXT DEFAULT '[]',
                    prompt_history_json TEXT DEFAULT '[]',
                    missions_json    TEXT DEFAULT '[]',
                    authors_json     TEXT DEFAULT '[]',
                    tags_json        TEXT DEFAULT '[]',
                    template_id      TEXT DEFAULT '',
                    parent_id        TEXT DEFAULT '',
                    html_output      TEXT DEFAULT '',
                    pdf_path         TEXT DEFAULT '',
                    docx_path        TEXT DEFAULT '',
                    report_id        TEXT DEFAULT '',
                    versions_json    TEXT DEFAULT '[]',
                    change_log_json  TEXT DEFAULT '[]',
                    updated_at       TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_proposals_status  ON proposals(status);
                CREATE INDEX IF NOT EXISTS idx_proposals_customer ON proposals(customer);
                CREATE INDEX IF NOT EXISTS idx_proposals_number   ON proposals(number);
                CREATE INDEX IF NOT EXISTS idx_proposals_date     ON proposals(date_created);
                """
            )

    def next_number(self, year: Optional[int] = None) -> str:
        if year is None:
            year = datetime.now().year
        with _LOCK:
            with self.conn_manager.connect(write=True) as conn:
                rows = conn.execute(
                    "SELECT number FROM proposals WHERE number LIKE ?",
                    (f"OFF-{year}-S%",),
                ).fetchall()
                max_seq = max((_seq_from_number(r["number"], year) for r in rows), default=130)
                candidate = max_seq + 1
                for _ in range(100000):
                    number = f"OFF-{year}-S{candidate:03d}"
                    exists = conn.execute("SELECT 1 FROM proposals WHERE number=?", (number,)).fetchone()
                    if not exists:
                        return number
                    candidate += 1
        raise RuntimeError("Failed to allocate next proposal number")

    def peek_next_number(self) -> int:
        year = datetime.now().year
        with self.conn_manager.connect(write=False) as conn:
            rows = conn.execute("SELECT number FROM proposals WHERE number LIKE ?", (f"OFF-{year}-S%",)).fetchall()
            max_seq = max((_seq_from_number(r["number"], year) for r in rows), default=130)
            return max_seq + 1

    @staticmethod
    def _proposal_to_row(p: Proposal) -> Dict[str, Any]:
        return {
            "id": p.id,
            "number": p.number,
            "title": p.title,
            "status": p.status,
            "version": p.version,
            "customer": p.customer,
            "customer_contact": p.customer_contact,
            "customer_email": p.customer_email,
            "customer_phone": p.customer_phone,
            "customer_address": p.customer_address,
            "customer_country": p.customer_country,
            "plant": p.plant,
            "language": p.language,
            "currency": p.currency,
            "responsible": p.responsible,
            "commercial": p.commercial,
            "project": p.project,
            "duration": p.duration,
            "validity_days": p.validity_days,
            "incoterm": p.incoterm,
            "payment_terms": p.payment_terms,
            "observations": p.observations,
            "date_created": p.date_created,
            "date_sent": p.date_sent,
            "date_accepted": p.date_accepted,
            "date_expiry": p.date_expiry,
            "services_json": json.dumps([s.__dict__ for s in p.services], default=str),
            "executive_summary": p.executive_summary,
            "about_ingecart": p.about_ingecart,
            "understanding_installation": p.understanding_installation,
            "objectives": p.objectives,
            "scope_of_services": p.scope_of_services,
            "maintenance_programme": p.maintenance_programme,
            "visit_methodology": p.visit_methodology,
            "deliverables": p.deliverables,
            "ingpro_section": p.ingpro_section,
            "optional_services": p.optional_services,
            "customer_responsibilities": p.customer_responsibilities,
            "commercial_conditions": p.commercial_conditions,
            "pricing_summary": p.pricing_summary,
            "why_ingecart": p.why_ingecart,
            "acceptance": p.acceptance,
            "annexes": p.annexes,
            "ai_comments_json": json.dumps(p.ai_comments),
            "prompt_history_json": json.dumps(p.prompt_history),
            "missions_json": json.dumps([m.__dict__ for m in p.missions], default=str),
            "authors_json": json.dumps(p.authors),
            "tags_json": json.dumps(p.tags),
            "template_id": p.template_id,
            "parent_id": p.parent_id,
            "html_output": p.html_output,
            "pdf_path": p.pdf_path,
            "docx_path": p.docx_path,
            "report_id": p.report_id,
            "versions_json": json.dumps([v.__dict__ for v in p.versions], default=str),
            "change_log_json": json.dumps(p.change_log),
            "updated_at": _now(),
        }

    @staticmethod
    def _row_to_proposal(row: sqlite3.Row) -> Proposal:
        d = dict(row)

        def _jl(key: str, default=None):
            try:
                return json.loads(d.get(key) or "[]")
            except Exception:
                return default or []

        services_data = _jl("services_json")
        services = [ServiceItem(**s) for s in services_data if isinstance(s, dict)]
        versions_data = _jl("versions_json")
        versions = [ProposalVersion(**v) for v in versions_data if isinstance(v, dict)]
        missions_data = _jl("missions_json")
        missions: list[MissionEntry] = []
        for m in missions_data:
            if isinstance(m, dict):
                try:
                    missions.append(MissionEntry(**m))
                except TypeError:
                    continue

        return Proposal(
            id=d.get("id", ""),
            number=d.get("number", ""),
            title=d.get("title", ""),
            status=d.get("status", "draft"),
            version=int(d.get("version", 1)),
            customer=d.get("customer", ""),
            customer_contact=d.get("customer_contact", ""),
            customer_email=d.get("customer_email", ""),
            customer_phone=d.get("customer_phone", ""),
            customer_address=d.get("customer_address", ""),
            customer_country=d.get("customer_country", ""),
            plant=d.get("plant", ""),
            language=d.get("language", "en"),
            currency=d.get("currency", "EUR"),
            responsible=d.get("responsible", "INGECART"),
            commercial=d.get("commercial", ""),
            project=d.get("project", ""),
            duration=d.get("duration", ""),
            validity_days=int(d.get("validity_days", 30)),
            incoterm=d.get("incoterm", ""),
            payment_terms=d.get("payment_terms", ""),
            observations=d.get("observations", ""),
            date_created=d.get("date_created", ""),
            date_sent=d.get("date_sent", ""),
            date_accepted=d.get("date_accepted", ""),
            date_expiry=d.get("date_expiry", ""),
            services=services,
            executive_summary=d.get("executive_summary", ""),
            about_ingecart=d.get("about_ingecart", ""),
            understanding_installation=d.get("understanding_installation", ""),
            objectives=d.get("objectives", ""),
            scope_of_services=d.get("scope_of_services", ""),
            maintenance_programme=d.get("maintenance_programme", ""),
            visit_methodology=d.get("visit_methodology", ""),
            deliverables=d.get("deliverables", ""),
            ingpro_section=d.get("ingpro_section", ""),
            optional_services=d.get("optional_services", ""),
            customer_responsibilities=d.get("customer_responsibilities", ""),
            commercial_conditions=d.get("commercial_conditions", ""),
            pricing_summary=d.get("pricing_summary", ""),
            why_ingecart=d.get("why_ingecart", ""),
            acceptance=d.get("acceptance", ""),
            annexes=d.get("annexes", ""),
            ai_comments=_jl("ai_comments_json"),
            prompt_history=_jl("prompt_history_json"),
            missions=missions,
            authors=_jl("authors_json"),
            tags=_jl("tags_json"),
            template_id=d.get("template_id", ""),
            parent_id=d.get("parent_id", ""),
            html_output=d.get("html_output", ""),
            pdf_path=d.get("pdf_path", ""),
            docx_path=d.get("docx_path", ""),
            report_id=d.get("report_id", ""),
            versions=versions,
            change_log=_jl("change_log_json"),
        )

    def create(self, proposal: Proposal) -> Proposal:
        if not proposal.id:
            proposal.id = str(uuid.uuid4())
        if not proposal.date_created:
            proposal.date_created = _now()

        attempts = 0
        while attempts < 20:
            attempts += 1
            if not proposal.number:
                proposal.number = self.next_number()
            row = self._proposal_to_row(proposal)
            cols = ", ".join(row.keys())
            placeholders = ", ".join(f":{k}" for k in row.keys())
            try:
                with _LOCK:
                    with self.conn_manager.connect(write=True) as conn:
                        conn.execute(f"INSERT INTO proposals ({cols}) VALUES ({placeholders})", row)
                return proposal
            except sqlite3.IntegrityError as exc:
                if "unique" in str(exc).lower() and "number" in str(exc).lower():
                    proposal.number = ""
                    continue
                raise
        raise RuntimeError("Could not create proposal after automatic number conflict resolution")

    def update(self, proposal: Proposal, change: str = "") -> Proposal:
        if change:
            proposal.change_log.append(f"[{_now()}] {change}")
        row = self._proposal_to_row(proposal)
        sets = ", ".join(f"{k}=:{k}" for k in row.keys() if k != "id")
        with _LOCK:
            with self.conn_manager.connect(write=True) as conn:
                conn.execute(f"UPDATE proposals SET {sets} WHERE id=:id", row)
        return proposal

    def get(self, proposal_id: str) -> Optional[Proposal]:
        with self.conn_manager.connect(write=False) as conn:
            row = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        return self._row_to_proposal(row) if row else None

    def get_by_number(self, number: str) -> Optional[Proposal]:
        with self.conn_manager.connect(write=False) as conn:
            row = conn.execute("SELECT * FROM proposals WHERE number=?", (number,)).fetchone()
        return self._row_to_proposal(row) if row else None

    def list_all(
        self,
        status: Optional[str] = None,
        customer: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 200,
    ) -> List[Proposal]:
        clauses = []
        params: List[Any] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if customer:
            clauses.append("LOWER(customer) LIKE ?")
            params.append(f"%{customer.lower()}%")
        if search:
            clauses.append("(LOWER(title) LIKE ? OR LOWER(customer) LIKE ? OR LOWER(number) LIKE ?)")
            s = f"%{search.lower()}%"
            params += [s, s, s]
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM proposals {where} ORDER BY date_created DESC LIMIT ?"
        params.append(limit)
        with self.conn_manager.connect(write=False) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_proposal(r) for r in rows]

    def delete(self, proposal_id: str) -> bool:
        with _LOCK:
            with self.conn_manager.connect(write=True) as conn:
                result = conn.execute("DELETE FROM proposals WHERE id=?", (proposal_id,))
        return result.rowcount > 0

    def duplicate(self, proposal_id: str, new_customer: Optional[str] = None) -> Optional[Proposal]:
        original = self.get(proposal_id)
        if not original:
            return None
        new_p = dataclasses.replace(original)
        new_p.id = str(uuid.uuid4())
        new_p.number = ""
        new_p.date_created = _now()
        new_p.date_sent = ""
        new_p.date_accepted = ""
        new_p.status = "draft"
        new_p.version = 1
        new_p.parent_id = original.id
        new_p.html_output = ""
        new_p.versions = []
        new_p.change_log = [f"[{_now()}] Duplicated from {original.number}"]
        if new_customer:
            new_p.customer = new_customer
        return self.create(new_p)

    def stats(self) -> Dict[str, Any]:
        with self.conn_manager.connect(write=False) as conn:
            total = conn.execute("SELECT COUNT(*) FROM proposals").fetchone()[0]
            by_status = {
                row[0]: row[1]
                for row in conn.execute("SELECT status, COUNT(*) FROM proposals GROUP BY status").fetchall()
            }
            total_value = conn.execute(
                "SELECT SUM(CAST(json_extract(s.value, '$.price') AS REAL) * "
                "COALESCE(CAST(json_extract(s.value, '$.quantity') AS REAL), 1.0)) "
                "FROM proposals p, json_each(p.services_json) s "
                "WHERE COALESCE(json_extract(s.value, '$.enabled'), 1) = 1"
            ).fetchone()[0] or 0.0
        next_n = self.peek_next_number()
        return {
            "total": total,
            "by_status": by_status,
            "total_value_eur": total_value,
            "next_number": f"OFF-{datetime.now().year}-S{next_n:03d}",
        }

    def database_health(self) -> dict[str, Any]:
        return self.conn_manager.health_report()

    def backup_database(self) -> str:
        return self.conn_manager.backup()
