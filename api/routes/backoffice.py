"""Backoffice API routes for administrative functions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

from backoffice.agents.backoffice_agent import backoffice

router = APIRouter(prefix="/backoffice", tags=["backoffice"])


class TaskCreate(BaseModel):
    title: str
    description: str
    assignee: str
    priority: str
    due_days: int = Field(ge=0, le=3650)


class InvoiceItem(BaseModel):
    description: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)


class InvoiceCreate(BaseModel):
    client_name: str
    client_email: str
    items: List[InvoiceItem]
    due_days: int = Field(default=30, ge=0, le=3650)


class EventCreate(BaseModel):
    title: str
    description: str
    start_time: datetime
    duration_hours: int = Field(ge=1, le=24)
    attendees: List[str]
    location: Optional[str] = None


class DocumentStore(BaseModel):
    filename: str
    file_path: str
    doc_type: str
    tags: List[str]
    metadata: Optional[Dict[str, Any]] = None


class EmailBulk(BaseModel):
    recipients: List[str]
    subject: str
    template: str
    context: Dict[str, Any]


class FormCreate(BaseModel):
    title: str
    fields: List[Dict[str, Any]]
    submit_action: str = "database"


class FormSubmission(BaseModel):
    form_id: str
    data: Dict[str, Any]
    respondent_email: str


@router.post("/tasks")
async def create_task(task: TaskCreate) -> Dict[str, Any]:
    result = backoffice.assign_task(
        title=task.title,
        description=task.description,
        assignee=task.assignee,
        priority=task.priority,
        due_days=task.due_days,
    )
    return {"status": "created", "task": result}


@router.get("/tasks")
async def get_tasks(status: Optional[str] = None, assignee: Optional[str] = None) -> Dict[str, Any]:
    tasks = backoffice.db.get_tasks(status=status, assigned_to=assignee)
    return {"tasks": tasks}


@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
    result = backoffice.complete_task(task_id, notes)
    return {"status": "completed", "task": result}


@router.post("/invoices")
async def create_invoice(invoice: InvoiceCreate) -> Dict[str, Any]:
    items = [item.model_dump() for item in invoice.items]
    result = backoffice.create_invoice(
        client_name=invoice.client_name,
        client_email=invoice.client_email,
        items=items,
        due_days=invoice.due_days,
    )
    return {"status": "created", "invoice": result}


@router.get("/invoices")
async def get_invoices(status: Optional[str] = None) -> Dict[str, Any]:
    invoices = backoffice.db.get_invoices(status=status)
    return {"invoices": invoices}


@router.get("/finance/summary")
async def get_financial_summary() -> Dict[str, Any]:
    return backoffice.get_financial_report()


@router.post("/calendar/events")
async def create_event(event: EventCreate) -> Dict[str, Any]:
    return backoffice.schedule_event(
        title=event.title,
        description=event.description,
        start=event.start_time,
        duration_hours=event.duration_hours,
        attendees=event.attendees,
        location=event.location,
    )


@router.get("/calendar/today")
async def get_today_schedule() -> Dict[str, Any]:
    events = backoffice.get_today_schedule()
    return {"events": events}


@router.post("/documents")
async def store_document(doc: DocumentStore) -> Dict[str, Any]:
    result = backoffice.store_document(
        filename=doc.filename,
        file_path=doc.file_path,
        doc_type=doc.doc_type,
        tags=doc.tags,
        metadata=doc.metadata,
    )
    return {"status": "stored", "document": result}


@router.get("/documents/search")
async def search_documents(q: str, doc_type: Optional[str] = None) -> Dict[str, Any]:
    docs = backoffice.search_documents(query=q, doc_type=doc_type)
    return {"documents": docs}


@router.post("/email/bulk")
async def send_bulk_emails(email_data: EmailBulk, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    background_tasks.add_task(
        backoffice.send_bulk_emails,
        email_data.recipients,
        email_data.subject,
        email_data.template,
        email_data.context,
    )
    return {"status": "sending", "recipient_count": len(email_data.recipients)}


@router.get("/email/check")
async def check_emails() -> Dict[str, Any]:
    responses = backoffice.check_emails_and_auto_respond()
    return {"processed": responses}


@router.post("/forms")
async def create_form(form: FormCreate) -> Dict[str, Any]:
    result = backoffice.create_form(
        title=form.title,
        fields=form.fields,
        submit_to=form.submit_action,
    )
    return {"status": "created", "form": result}


@router.post("/forms/submit")
async def submit_form(submission: FormSubmission) -> Dict[str, Any]:
    result = backoffice.process_form_submission(
        form_id=submission.form_id,
        data=submission.data,
        respondent=submission.respondent_email,
    )
    return {"status": "received", "submission": result}


@router.get("/reports/daily")
async def daily_report(assignee_email: str = "isenar.cta@gmail.com") -> Dict[str, Any]:
    report = backoffice.generate_daily_report(assignee_email=assignee_email)
    return {"generated_at": datetime.now().isoformat(), "report": report}
