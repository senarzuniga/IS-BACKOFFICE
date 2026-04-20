"""Reporting API routes."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from backoffice.reporting.generator import ReportGenerator
from api.state import graph_store

router = APIRouter(prefix="/reports", tags=["reporting"])


@router.get("/executive")
def executive_report():
    return ReportGenerator(graph_store).executive_summary()


@router.get("/executive/html", response_class=HTMLResponse)
def executive_report_html():
    gen = ReportGenerator(graph_store)
    report = gen.executive_summary()
    return gen.to_html(report)


@router.get("/clients/{client_id}/diagnostic")
def client_diagnostic(client_id: str):
    return ReportGenerator(graph_store).client_diagnostic(client_id)


@router.get("/sales-performance")
def sales_performance():
    return ReportGenerator(graph_store).sales_performance()
