"""Supabase-backed database client with in-memory fallback."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv() -> bool:  # type: ignore[override]
        return False

try:
    from supabase import Client, create_client
except Exception:  # pragma: no cover
    Client = Any  # type: ignore[misc,assignment]
    create_client = None


load_dotenv()


class SupabaseBackofficeClient:
    """Main database client for backoffice operations."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL", "https://wbndbwtcwkianwhrdlei.supabase.co")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        self.client: Optional[Client] = None
        if create_client and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
            except Exception:
                self.client = None

        self._memory: Dict[str, List[Dict[str, Any]]] = {
            "tasks": [],
            "invoices": [],
            "payments": [],
            "documents": [],
            "calendar_events": [],
            "forms": [],
            "form_submissions": [],
            "email_logs": [],
        }

    def is_connected(self) -> bool:
        return self.client is not None

    # ============ ADMINISTRATION ============

    def create_task(
        self,
        title: str,
        description: str,
        assigned_to: str,
        priority: str,
        due_date: date,
        status: str = "pending",
    ) -> Dict[str, Any]:
        task = {
            "id": str(uuid4()),
            "title": title,
            "description": description,
            "assigned_to": assigned_to,
            "priority": priority,
            "status": status,
            "due_date": due_date.isoformat(),
            "created_at": datetime.now().isoformat(),
            "created_by": "system",
            "notes": None,
        }
        return self._insert("tasks", task)

    def get_tasks(self, status: Optional[str] = None, assigned_to: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self._select_all("tasks")
        if status:
            rows = [r for r in rows if r.get("status") == status]
        if assigned_to:
            rows = [r for r in rows if r.get("assigned_to") == assigned_to]
        return sorted(rows, key=lambda r: r.get("due_date", ""))

    def update_task_status(self, task_id: str, status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        update_data: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now().isoformat(),
        }
        if notes:
            update_data["notes"] = notes
        return self._update_by_id("tasks", task_id, update_data)

    # ============ FINANCING & INVOICING ============

    def create_invoice(
        self,
        client_name: str,
        client_email: str,
        items: List[Dict[str, Any]],
        due_date: date,
        tax_rate: float = 21.0,
        currency: str = "EUR",
    ) -> Dict[str, Any]:
        subtotal = sum(float(item.get("quantity", 0)) * float(item.get("unit_price", 0)) for item in items)
        tax_amount = subtotal * (tax_rate / 100.0)
        total = subtotal + tax_amount

        invoice = {
            "id": str(uuid4()),
            "invoice_number": self._generate_invoice_number(),
            "client_name": client_name,
            "client_email": client_email,
            "items": items,
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total": total,
            "currency": currency,
            "status": "draft",
            "issue_date": date.today().isoformat(),
            "due_date": due_date.isoformat(),
            "created_at": datetime.now().isoformat(),
        }
        return self._insert("invoices", invoice)

    def get_invoices(self, status: Optional[str] = None, client_email: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = self._select_all("invoices")
        if status:
            rows = [r for r in rows if r.get("status") == status]
        if client_email:
            rows = [r for r in rows if r.get("client_email") == client_email]
        return sorted(rows, key=lambda r: r.get("issue_date", ""), reverse=True)

    def record_payment(
        self,
        invoice_id: str,
        amount: float,
        payment_method: str,
        transaction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        payment = {
            "id": str(uuid4()),
            "invoice_id": invoice_id,
            "amount": amount,
            "payment_method": payment_method,
            "transaction_id": transaction_id,
            "payment_date": datetime.now().isoformat(),
            "status": "completed",
        }
        created = self._insert("payments", payment)
        self._update_by_id("invoices", invoice_id, {"status": "paid", "updated_at": datetime.now().isoformat()})
        return created

    def get_financial_summary(self, year: int, month: Optional[int] = None) -> Dict[str, Any]:
        completed = [p for p in self._select_all("payments") if p.get("status") == "completed"]
        if month:
            month_prefix = f"{year:04d}-{month:02d}"
            completed = [p for p in completed if str(p.get("payment_date", "")).startswith(month_prefix)]
        else:
            completed = [p for p in completed if str(p.get("payment_date", "")).startswith(f"{year:04d}-")]

        total_revenue = sum(float(p.get("amount", 0)) for p in completed)
        total_pending = sum(float(i.get("total", 0)) for i in self.get_invoices(status="sent"))
        return {
            "total_revenue": total_revenue,
            "pending_invoices": total_pending,
            "total_transactions": len(completed),
            "currency": "EUR",
        }

    # ============ DOCUMENT STORAGE ============

    def store_document(
        self,
        filename: str,
        file_path: str,
        document_type: str,
        tags: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        doc_record = {
            "id": str(uuid4()),
            "filename": filename,
            "file_path": file_path,
            "document_type": document_type,
            "tags": tags,
            "metadata": metadata or {},
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "created_by": "system",
        }
        return self._insert("documents", doc_record)

    def get_documents(
        self,
        document_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._select_all("documents")
        if document_type:
            rows = [r for r in rows if r.get("document_type") == document_type]
        if tags:
            tag_set = {t.lower() for t in tags}
            rows = [r for r in rows if tag_set.intersection({x.lower() for x in r.get("tags", [])})]
        return sorted(rows, key=lambda r: r.get("created_at", ""), reverse=True)

    # ============ CALENDAR & AGENDA ============

    def create_event(
        self,
        title: str,
        description: str,
        start_time: datetime,
        end_time: datetime,
        attendees: List[str],
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        event = {
            "id": str(uuid4()),
            "title": title,
            "description": description,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "attendees": attendees,
            "location": location,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
        }
        return self._insert("calendar_events", event)

    def get_upcoming_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        now = datetime.now()
        future = now + timedelta(days=days_ahead)
        rows = self._select_all("calendar_events")
        filtered: List[Dict[str, Any]] = []
        for row in rows:
            try:
                start = datetime.fromisoformat(row["start_time"])
            except Exception:
                continue
            if now <= start <= future:
                filtered.append(row)
        return sorted(filtered, key=lambda r: r.get("start_time", ""))

    # ============ FORMS MANAGEMENT ============

    def create_form(self, title: str, fields: List[Dict[str, Any]], submit_action: str) -> Dict[str, Any]:
        form = {
            "id": str(uuid4()),
            "title": title,
            "fields": fields,
            "submit_action": submit_action,
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "is_active": True,
        }
        return self._insert("forms", form)

    def submit_form_response(self, form_id: str, response_data: Dict[str, Any], respondent_email: str) -> Dict[str, Any]:
        submission = {
            "id": str(uuid4()),
            "form_id": form_id,
            "response_data": response_data,
            "respondent_email": respondent_email,
            "submitted_at": datetime.now().isoformat(),
            "status": "received",
        }
        return self._insert("form_submissions", submission)

    # ============ EMAIL MANAGEMENT ============

    def log_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        direction: str,
        status: str = "sent",
    ) -> Dict[str, Any]:
        email_log = {
            "id": str(uuid4()),
            "to_email": to_email,
            "subject": subject,
            "body": body[:1000],
            "direction": direction,
            "status": status,
            "sent_at": datetime.now().isoformat(),
            "is_read": False,
        }
        return self._insert("email_logs", email_log)

    # ============ HELPERS ============

    def _generate_invoice_number(self) -> str:
        year = datetime.now().year
        month = datetime.now().month
        prefix = f"INV-{year}{month:02d}"
        count = len([i for i in self._select_all("invoices") if str(i.get("invoice_number", "")).startswith(prefix)])
        return f"{prefix}-{count + 1:04d}"

    def _insert(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        if self.client:
            try:
                result = self.client.table(table).insert(row).execute()
                if getattr(result, "data", None):
                    return result.data[0]
            except Exception:
                pass
        self._memory[table].append(row)
        return row

    def _select_all(self, table: str) -> List[Dict[str, Any]]:
        if self.client:
            try:
                result = self.client.table(table).select("*").execute()
                if isinstance(getattr(result, "data", None), list):
                    return result.data
            except Exception:
                pass
        return list(self._memory[table])

    def _update_by_id(self, table: str, row_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if self.client:
            try:
                result = self.client.table(table).update(updates).eq("id", row_id).execute()
                if getattr(result, "data", None):
                    return result.data[0]
            except Exception:
                pass

        for row in self._memory[table]:
            if row.get("id") == row_id:
                row.update(updates)
                return row
        return {}


supabase_db = SupabaseBackofficeClient()
