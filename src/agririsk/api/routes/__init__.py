"""API routes package."""

from agririsk.api.routes.health import router as health_router
from agririsk.api.routes.counties import router as counties_router

__all__ = ["health_router", "counties_router"]
