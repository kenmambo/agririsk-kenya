"""Initial database migration and setup script for AgriRisk Kenya.

Usage:
    uv run python scripts/setup_db.py [--reset]

This script:
1. Initializes database tables registered in SQLAlchemy models (Milestone 1: Counties).
2. Seeds the reference data for all 47 counties of Kenya.
"""

import argparse
import sys
from typing import Optional
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from agririsk.core.logging import logger
from agririsk.core.config import settings
from agririsk.core.database import (
    Base,
    County,
    get_engine,
    init_db,
    SessionLocal,
    seed_counties,
)


def setup_database(target_engine: Optional[Engine] = None, reset: bool = False) -> int:
    """Initialize database schema and seed the official 47 Kenya counties.

    Args:
        target_engine: Optional SQLAlchemy engine. Defaults to project configured engine.
        reset: If True, drop existing tables before creating schema.

    Returns:
        Number of county records added.
    """
    eng = target_engine or get_engine()
    logger.info("Setting up database at: %s", settings.database.url)

    if reset:
        logger.warning("Reset flag detected: dropping all existing tables...")
        Base.metadata.drop_all(bind=eng)

    logger.info("Creating database tables...")
    init_db(target_engine=eng)

    logger.info("Seeding reference county records...")
    Session = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    with Session() as session:
        added_count = seed_counties(session)
        total_count = session.query(County).count()
        logger.info("Seeding complete. New counties added: %d. Total counties in DB: %d.", added_count, total_count)

    return added_count


def parse_args() -> argparse.Namespace:
    """Parse command line flags."""
    parser = argparse.ArgumentParser(description="AgriRisk Kenya Database Setup")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables before recreating schema and seeding."
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for database setup CLI."""
    args = parse_args()
    try:
        setup_database(reset=args.reset)
        logger.info("Database setup successfully completed.")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
