"""Health check endpoint for AgriRisk Kenya API."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from agririsk.core.config import settings
from agririsk.core.database import get_db
from agririsk.version import APP_VERSION, MODEL_VERSION, DATASET_VERSION, RELEASE_DATE
from agririsk.validation.schemas import HealthResponse, VersionResponse

router = APIRouter(tags=["Health & Metadata"])


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Check API, database connectivity, and model/dataset versions."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        app_name=settings.project_name,
        version=APP_VERSION,
        app_version=APP_VERSION,
        model_version=MODEL_VERSION,
        dataset_version=DATASET_VERSION,
        environment=settings.app_env,
        database_status=db_status,
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/version", response_model=VersionResponse)
def get_version() -> VersionResponse:
    """Retrieve application semantic version, model version, and build info."""
    return VersionResponse(
        app_name=settings.project_name,
        app_version=APP_VERSION,
        model_version=MODEL_VERSION,
        dataset_version=DATASET_VERSION,
        release_date=RELEASE_DATE,
        environment=settings.app_env,
        repository="https://github.com/kenmambo/agririsk-kenya"
    )
