"""Unit tests for SQLAlchemy database models and setup in Milestone 1."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from agririsk.core.database import (
    Base,
    County,
    init_db,
    seed_counties,
)
from scripts.setup_db import setup_database


def test_counties_seeded(db_session):
    """Verify that all 47 counties are seeded correctly."""
    count = db_session.query(County).count()
    assert count == 47

    turkana = db_session.query(County).filter_by(code="023").first()
    assert turkana is not None
    assert turkana.name == "Turkana"
    assert turkana.asal_category == "Arid"
    assert turkana.centroid_lat == 3.1167
    assert turkana.centroid_lon == 35.6


def test_county_unique_code_constraint(db_session):
    """Verify that duplicate county codes raise an IntegrityError."""
    duplicate_code_county = County(
        code="001",  # Mombasa already exists
        name="Duplicate Mombasa",
        asal_category="Non-ASAL",
        centroid_lat=-4.0,
        centroid_lon=39.6
    )
    db_session.add(duplicate_code_county)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_county_unique_name_constraint(db_session):
    """Verify that duplicate county names raise an IntegrityError."""
    duplicate_name_county = County(
        code="999",
        name="Mombasa",  # Mombasa name already exists
        asal_category="Non-ASAL",
        centroid_lat=-4.0,
        centroid_lon=39.6
    )
    db_session.add(duplicate_name_county)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_county_repr():
    """Verify string representation of County instance."""
    county = County(code="023", name="Turkana", asal_category="Arid", centroid_lat=3.1, centroid_lon=35.6)
    assert repr(county) == "<County(code='023', name='Turkana', asal='Arid')>"


def test_init_db_creates_tables():
    """Verify init_db initializes schema on a fresh engine."""
    engine = create_engine("sqlite:///:memory:")
    init_db(target_engine=engine)
    assert "counties" in Base.metadata.tables


def test_setup_database_script_function():
    """Verify setup_database function creates tables and seeds counties."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    added = setup_database(target_engine=test_engine, reset=True)
    assert added == 47

    Session = sessionmaker(bind=test_engine)
    with Session() as session:
        count = session.query(County).count()
        assert count == 47
