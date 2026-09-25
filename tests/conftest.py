"""Pytest fixtures and test environment configuration for Milestone 1."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from agririsk.core.config import Settings
from agririsk.core.database import Base, seed_counties, get_db
from agririsk.api.app import create_app


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide isolated test settings."""
    return Settings.from_yaml_and_env(env_name="test")


@pytest.fixture(scope="function")
def in_memory_engine():
    """Create a fresh in-memory SQLite database engine using StaticPool for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(in_memory_engine):
    """Provide a scoped session linked to the in-memory database with seeded counties."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=in_memory_engine)
    session = SessionLocal()
    seed_counties(session)
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_client(in_memory_engine) -> TestClient:
    """Provide a FastAPI TestClient configured to use the in-memory database."""
    app = create_app()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=in_memory_engine)

    # Seed reference counties in the in-memory test database
    with TestingSessionLocal() as session:
        seed_counties(session)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
