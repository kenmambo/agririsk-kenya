"""FastAPI application factory for AgriRisk Kenya."""

from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from agririsk.core.config import settings
from agririsk.core.logging import logger
from agririsk.core.database import init_db, SessionLocal, seed_counties
from agririsk.api.routes.health import router as health_router
from agririsk.api.routes.counties import router as counties_router
from agririsk.api.routes.risk import router as risk_router
from agririsk.forecasting.artifact_loader import ModelArtifactError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    logger.info("Starting up %s (env=%s, mode=%s)...", settings.project_name, settings.app_env, settings.agririsk_mode)
    init_db()
    with SessionLocal() as db:
        seeded = seed_counties(db)
        if seeded > 0:
            logger.info("Seeded %d Kenya counties into database.", seeded)
    yield
    logger.info("Shutting down %s...", settings.project_name)


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.api.title,
        version=settings.version,
        description=(
            "AgriRisk Kenya REST API: Automated early-warning and decision-support prototype "
            "for climate-resilient agriculture and food security in Kenya's ASALs."
        ),
        lifespan=lifespan,
    )

    # Cross-Origin Resource Sharing (CORS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request processing latency logger middleware
    @app.middleware("http")
    async def log_request_metrics(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000.0
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
        logger.info(
            "HTTP %s %s [%d] in %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            process_time
        )
        return response

    # User-friendly error handlers preventing internal traceback leaks
    @app.exception_handler(ModelArtifactError)
    async def model_artifact_error_handler(request: Request, exc: ModelArtifactError):
        logger.error("ModelArtifactError at %s: %s", request.url.path, str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "error": "ModelUnavailable",
                "message": "Forecast unavailable because the model artefact could not be loaded.",
                "detail": str(exc),
            }
        )

    # Include Versioned Endpoints (/api/v1/...)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(counties_router, prefix="/api/v1")
    app.include_router(risk_router, prefix="/api/v1")

    # Direct Root Availability for Top-Level Endpoints
    app.include_router(health_router)
    app.include_router(risk_router)

    return app


app = create_app()
