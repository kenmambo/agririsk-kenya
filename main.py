"""AgriRisk Kenya - Command Line Entry Point for Milestone 1."""

import sys
from agririsk.core.config import settings
from agririsk.core.logging import logger
from agririsk.core.database import SessionLocal, County


def main() -> None:
    """Print project status and quick-start instructions."""
    logger.info("Initializing %s (v%s, env=%s)...", settings.project_name, settings.version, settings.app_env)

    try:
        with SessionLocal() as db:
            county_count = db.query(County).count()
            logger.info("Database connection: ACTIVE. Counties registered: %d", county_count)
    except Exception as e:
        logger.warning("Database connection failed or not initialized: %s", e)
        print("\nTip: Run 'uv run python scripts/setup_db.py' to initialize and seed the database.\n")

    print("\n" + "=" * 60)
    print(f"[{settings.project_name}] - Milestone 1")
    print("=" * 60)
    print(f"- Environment: {settings.app_env}")
    print(f"- Database URI: {settings.database.url}")
    print(f"- API Host/Port: {settings.api.host}:{settings.api.port}")
    print("\nCommands:")
    print("  1. Run Database Setup & Seeding:  uv run python scripts/setup_db.py")
    print("  2. Run Test Suite:                 uv run pytest")
    print("  3. Launch FastAPI Backend:         uv run uvicorn agririsk.api.app:app --reload")
    print("  4. Launch Streamlit Home Page:     uv run streamlit run src/agririsk/ui/streamlit_app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
