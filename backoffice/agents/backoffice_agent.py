"""Unified Backoffice Agent for administrative workflows."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from backoffice.database.supabase_client import supabase_db
from backoffice.integrations.google_integration import google


class BackofficeAgent:
    """Master agent for all backoffice operations."""

    def __init__(self) -> None:
        self.db = supabase_db
        self.google = google

    # ============ ADMINISTRATION ============

    def assign_task(self, title: str, description: str, assignee: str, priority: str, due_days: int) -> Dict[str, Any]:
        due_date = date.today() + timedelta(days=due_days)
        task = self.db.create_task(
            title=title,
            description=description,
            assigned_to=assignee,
            priority=priority,
            due_date=due_date,
        )
        self._send_notification(
            to=assignee if "@" in assignee else f"{assignee}@gmail.com",
            subject=f"New Task Assigned: {title}",
            body=f"You have been assigned a {priority} priority task:\n\n{description}\n\nDue: {due_date}",
        )
        return task

    def get_my_tasks(self, email: str) -> List[Dict[str, Any]]:
        return self.db.get_tasks(assigned_to=email)

    def complete_task(self, task_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        return self.db.update_task_status(task_id, "completed", notes)

    # ============ INVOICING & FINANCE ============

    def create_invoice(
        self,
        client_name: str,
        client_email: str,
        items: List[Dict[str, Any]],
        due_days: int = 30,
    ) -> Dict[str, Any]:
        due_date = date.today() + timedelta(days=due_days)
        invoice = self.db.create_invoice(
            client_name=client_name,
            client_email=client_email,
            items=items,
            due_date=due_date,
        )
        if invoice:
            invoice_html = self._generate_invoice_html(invoice)
            self.google.send_email(
                to=client_email,
                subject=f"Invoice {invoice.get('invoice_number', '')} from CTA",
                body=invoice_html,
                html=True,
            )
        return invoice

    def get_financial_report(self) -> Dict[str, Any]:
        summary = self.db.get_financial_summary(datetime.now().year)
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "pending_invoices": self.db.get_invoices(status="sent"),
            "recent_paid_invoices": self.db.get_invoices(status="paid")[:10],
        }

    # ============ DOCUMENT MANAGEMENT ============

    def store_document(
        self,
        filename: str,
        file_path: str,
        doc_type: str,
        tags: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.db.store_document(filename, file_path, doc_type, tags, metadata)

    def search_documents(self, query: str, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        docs = self.db.get_documents(document_type=doc_type)
        if not query:
            return docs
        q = query.lower()
        return [
            d
            for d in docs
            if q in str(d.get("filename", "")).lower() or q in str(d.get("tags", [])).lower()
        ]

    # ============ CALENDAR & SCHEDULING ============

    def schedule_event(
        self,
        title: str,
        description: str,
        start: datetime,
        duration_hours: int,
        attendees: List[str],
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        end = start + timedelta(hours=duration_hours)
        google_event = self.google.create_event(
            summary=title,
            description=description,
            start_time=start,
            end_time=end,
            attendees=attendees,
            location=location,
        )
        db_event = self.db.create_event(
            title=title,
            description=description,
            start_time=start,
            end_time=end,
            attendees=attendees,
            location=location,
        )
        return {"google_event": google_event, "db_event": db_event}

    def get_today_schedule(self) -> List[Dict[str, Any]]:
        return self.db.get_upcoming_events(days_ahead=1)

    # ============ EMAIL AUTOMATION ============

    def send_bulk_emails(
        self,
        recipients: List[str],
        subject: str,
        template: str,
        context: Dict[str, Any],
    ) -> List[bool]:
        results: List[bool] = []
        for recipient in recipients:
            personalized = template
            for key, value in context.items():
                personalized = personalized.replace(f"{{{{{key}}}}}", str(value))

            sent = self.google.send_email(to=recipient, subject=subject, body=personalized, html=True)
            results.append(sent)
            self.db.log_email(
                to_email=recipient,
                subject=subject,
                body=personalized,
                direction="outgoing",
                status="sent" if sent else "failed",
            )
        return results

    def check_emails_and_auto_respond(self) -> List[Dict[str, Any]]:
        unread = self.google.get_unread_emails(max_results=20)
        responses: List[Dict[str, Any]] = []

        for email in unread:
            subject = str(email.get("subject", "")).lower()
            sender = str(email.get("from", ""))
            if "invoice" in subject:
                self.google.send_email(
                    to=sender,
                    subject="RE: Invoice Information",
                    body="Your invoice has been received. We will process it within 24 hours.",
                )
                responses.append({"type": "invoice", "email": sender})
            elif "meeting" in subject:
                responses.append({"type": "meeting_request", "email": sender})

        return responses

    # ============ FORMS & DATA COLLECTION ============

    def create_form(self, title: str, fields: List[Dict[str, Any]], submit_to: str = "database") -> Dict[str, Any]:
        return self.db.create_form(title, fields, submit_to)

    def process_form_submission(self, form_id: str, data: Dict[str, Any], respondent: str) -> Dict[str, Any]:
        submission = self.db.submit_form_response(form_id, data, respondent)
        if "invoice_request" in form_id:
            self.create_invoice(
                client_name=str(data.get("name", "Unknown Client")),
                client_email=respondent,
                items=[
                    {
                        "description": str(data.get("service", "Service")),
                        "quantity": 1,
                        "unit_price": float(data.get("amount", 0) or 0),
                    }
                ],
            )
        return submission

    # ============ REPORTING ============

    def generate_daily_report(self, assignee_email: str = "isenar.cta@gmail.com") -> str:
        tasks = self.db.get_tasks(status="completed", assigned_to=assignee_email)
        events = self.db.get_upcoming_events(days_ahead=1)
        invoices = self.db.get_invoices(status="sent")
        return (
            f"# Daily Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"
            f"## Tasks Completed Today: {len(tasks)}\n"
            f"{self._format_tasks(tasks)}\n\n"
            f"## Today's Schedule: {len(events)} events\n"
            f"{self._format_events(events)}\n\n"
            f"## Pending Invoices: {len(invoices)}\n"
            f"Total Amount: {sum(float(i.get('total', 0)) for i in invoices):.2f} EUR\n\n"
            "## Next Actions\n"
            "- Review pending invoices\n"
            "- Follow up on open tasks\n"
            "- Prepare for tomorrow's meetings\n"
        )

    # ============ HELPERS ============

    def _send_notification(self, to: str, subject: str, body: str) -> None:
        self.google.send_email(to=to, subject=subject, body=body)

    def _generate_invoice_html(self, invoice: Dict[str, Any]) -> str:
        items_html = ""
        for item in invoice.get("items", []):
            qty = float(item.get("quantity", 0) or 0)
            unit = float(item.get("unit_price", 0) or 0)
            items_html += (
                "<tr>"
                f"<td>{item.get('description', '')}</td>"
                f"<td>{qty:g}</td>"
                f"<td>{unit:.2f} {invoice.get('currency', 'EUR')}</td>"
                f"<td>{qty * unit:.2f} {invoice.get('currency', 'EUR')}</td>"
                "</tr>"
            )

        return (
            "<html><body>"
            f"<h2>Invoice {invoice.get('invoice_number', '')}</h2>"
            f"<p><strong>Client:</strong> {invoice.get('client_name', '')}</p>"
            f"<p><strong>Issue Date:</strong> {invoice.get('issue_date', '')}</p>"
            f"<p><strong>Due Date:</strong> {invoice.get('due_date', '')}</p>"
            "<table border='1' cellpadding='5'>"
            "<tr><th>Description</th><th>Quantity</th><th>Unit Price</th><th>Total</th></tr>"
            f"{items_html}"
            "<tr><td colspan='3' align='right'><strong>Subtotal:</strong></td>"
            f"<td>{float(invoice.get('subtotal', 0)):.2f} {invoice.get('currency', 'EUR')}</td></tr>"
            "<tr><td colspan='3' align='right'><strong>Tax:</strong></td>"
            f"<td>{float(invoice.get('tax_amount', 0)):.2f} {invoice.get('currency', 'EUR')}</td></tr>"
            "<tr><td colspan='3' align='right'><strong>Total:</strong></td>"
            f"<td><strong>{float(invoice.get('total', 0)):.2f} {invoice.get('currency', 'EUR')}</strong></td></tr>"
            "</table>"
            "</body></html>"
        )

    def _format_tasks(self, tasks: List[Dict[str, Any]]) -> str:
        if not tasks:
            return "No tasks completed today."
        return "\n".join(f"- {t.get('title', 'Untitled')}: {t.get('notes') or 'Completed'}" for t in tasks)

    def _format_events(self, events: List[Dict[str, Any]]) -> str:
        if not events:
            return "No scheduled events."
        return "\n".join(f"- {e.get('title', 'Event')} at {e.get('start_time', '')}" for e in events)


backoffice = BackofficeAgent()
