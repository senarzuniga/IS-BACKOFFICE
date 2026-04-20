"""FastAPI application entry point."""
from fastapi import FastAPI
from api.routes.ingestion import router as ingestion_router
from api.routes.graph import router as graph_router
from api.routes.analytics import router as analytics_router
from api.routes.reporting import router as reporting_router
from api.routes.review import router as review_router

app = FastAPI(
    title="IS-BACKOFFICE – AI Commercial Intelligence Platform",
    version="1.0.0",
    description="Modular AI-powered back-office system for strategic consulting firms.",
)

app.include_router(ingestion_router)
app.include_router(graph_router)
app.include_router(analytics_router)
app.include_router(reporting_router)
app.include_router(review_router)


@app.get("/")
def root():
    return {
        "system": "IS-BACKOFFICE",
        "version": "1.0.0",
        "modules": ["ingestion", "cleaning", "extraction", "graph", "analytics", "reporting"],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
