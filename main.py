"""FastAPI application entry point."""
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from api.routes.ingestion import router as ingestion_router
from api.routes.graph import router as graph_router
from api.routes.analytics import router as analytics_router
from api.routes.reporting import router as reporting_router
from api.routes.review import router as review_router
from api.routes.orchestration import router as orchestration_router

app = FastAPI(
    title="IS-BACKOFFICE – AI Commercial Intelligence Platform",
    version="1.0.0",
    description="Modular AI-powered back-office system for strategic consulting firms.",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app.include_router(ingestion_router, dependencies=[Depends(oauth2_scheme)])
app.include_router(graph_router, dependencies=[Depends(oauth2_scheme)])
app.include_router(analytics_router, dependencies=[Depends(oauth2_scheme)])
app.include_router(reporting_router, dependencies=[Depends(oauth2_scheme)])
app.include_router(review_router, dependencies=[Depends(oauth2_scheme)])
app.include_router(orchestration_router, dependencies=[Depends(oauth2_scheme)])


@app.get("/")
def root():
    return {
        "system": "IS-BACKOFFICE",
        "version": "1.0.0",
        "modules": ["ingestion", "cleaning", "extraction", "graph", "analytics", "reporting", "orchestration"],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
