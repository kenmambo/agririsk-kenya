"""FastAPI application factory for AgriRisk Kenya."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agririsk.core.config import settings
from agririsk.core.logging import logger
from agririsk.core.database import init_db, get_engine, SessionLocal, seed_counties
from agririsk.api.routes.health import router as health_router
from agririsk.api.routes.counties import router as counties_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown hooks."""
    logger.info("Starting up %s (env=%s)...", settings.project_name, settings.app_env)
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
        description="County-level early-warning and decision-support prototype for climate-resilient agriculture and food security in Kenya.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(health_router)  # Direct /health availability
    app.include_router(counties_router, prefix="/api/v1")

    return app


app = create_app()
