"""Health check endpoint for AgriRisk Kenya API."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from agririsk.core.config import settings
from agririsk.core.database import get_db
from agririsk.validation.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Check API and database health status."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        app_name=settings.project_name,
        version=settings.version,
        environment=settings.app_env,
        database_status=db_status,
        timestamp=datetime.now(timezone.utc)
    )
