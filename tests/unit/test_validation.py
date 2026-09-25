"""Unit tests for Pydantic schema validation in Milestone 1."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from agririsk.validation.schemas import (
    CountyBase,
    CountyCreate,
    CountyRead,
    HealthResponse,
)


def test_valid_county_schema():
    """Verify valid county data validation and code formatting."""
    c = CountyBase(
        code="1",  # Coerces to '001'
        name="Mombasa",
        asal_category="Non-ASAL",
        centroid_lat=-4.0435,
        centroid_lon=39.6682
    )
    assert c.code == "001"
    assert c.name == "Mombasa"
    assert c.asal_category == "Non-ASAL"


def test_invalid_county_code_rejected():
    """Verify rejection of non-existent Kenya county code."""
    with pytest.raises(ValidationError):
        CountyBase(
            code="999",
            name="Non-Existent",
            asal_category="Arid",
            centroid_lat=0.0,
            centroid_lon=37.0
        )


def test_invalid_asal_category_rejected():
    """Verify rejection of invalid ASAL category."""
    with pytest.raises(ValidationError):
        CountyBase(
            code="023",
            name="Turkana",
            asal_category="Highland",  # Not in Literal['Arid', 'Semi-Arid', 'Non-ASAL']
            centroid_lat=3.1167,
            centroid_lon=35.6
        )


def test_latitude_out_of_kenya_bounds():
    """Verify rejection of coordinates outside Kenya geographical boundaries."""
    with pytest.raises(ValidationError):
        CountyBase(
            code="023",
            name="Turkana",
            asal_category="Arid",
            centroid_lat=25.0,  # Far outside Kenya bounds [-5.0, 5.5]
            centroid_lon=35.6
        )


def test_longitude_out_of_kenya_bounds():
    """Verify rejection of longitude outside Kenya boundaries."""
    with pytest.raises(ValidationError):
        CountyBase(
            code="023",
            name="Turkana",
            asal_category="Arid",
            centroid_lat=1.0,
            centroid_lon=10.0  # Far outside Kenya bounds [33.5, 42.5]
        )


def test_county_read_serialization():
    """Verify serialization of CountyRead model."""
    data = {
        "code": "047",
        "name": "Nairobi",
        "asal_category": "Non-ASAL",
        "centroid_lat": -1.2921,
        "centroid_lon": 36.8219
    }
    county_read = CountyRead(**data)
    assert county_read.code == "047"
    assert county_read.name == "Nairobi"


def test_health_response_schema():
    """Verify valid HealthResponse schema parsing."""
    hr = HealthResponse(
        status="healthy",
        app_name="AgriRisk Kenya",
        version="0.1.0",
        environment="test",
        database_status="connected",
        timestamp=datetime.now(timezone.utc)
    )
    assert hr.status == "healthy"
    assert hr.database_status == "connected"
