"""FastAPI application entry point."""
from typing import Optional

from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from api.routes.ingestion import router as ingestion_router
from api.routes.graph import router as graph_router
from api.routes.analytics import router as analytics_router
from api.routes.reporting import router as reporting_router
from api.routes.review import router as review_router
from api.routes.orchestration import router as orchestration_router
from api.routes.backoffice import router as backoffice_router
from api.routes.intelligence_ingestion import router as intelligence_ingestion_router

app = FastAPI(
    title="IS-BACKOFFICE – AI Commercial Intelligence Platform",
    version="1.0.0",
    description="Modular AI-powered back-office system for strategic consulting firms.",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)


def optional_oauth_token(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Keep bearer parsing enabled without rejecting anonymous requests by default."""
    return token

app.include_router(ingestion_router, dependencies=[Depends(optional_oauth_token)])
app.include_router(graph_router, dependencies=[Depends(optional_oauth_token)])
app.include_router(analytics_router, dependencies=[Depends(optional_oauth_token)])
app.include_router(reporting_router, dependencies=[Depends(optional_oauth_token)])
app.include_router(review_router, dependencies=[Depends(optional_oauth_token)])
app.include_router(orchestration_router, dependencies=[Depends(optional_oauth_token)])
app.include_router(backoffice_router, dependencies=[Depends(optional_oauth_token)])
app.include_router(intelligence_ingestion_router, dependencies=[Depends(optional_oauth_token)])


@app.get("/")
def root():
    return {
        "system": "IS-BACKOFFICE",
        "version": "1.0.0",
        "modules": ["ingestion", "cleaning", "extraction", "graph", "analytics", "reporting", "orchestration", "backoffice", "intelligence_ingestion"],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
