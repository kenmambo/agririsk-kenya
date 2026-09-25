"""Unit tests for deployment, FastAPI versioning, risk endpoints, and model artifact management."""

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from agririsk.api.app import app
from agririsk.version import APP_VERSION, MODEL_VERSION, DATASET_VERSION
from agririsk.forecasting.artifact_loader import ModelArtifactManager, ModelArtifactError


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


def test_health_endpoint_contract(client):
    """Verify that /health returns all required version metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["app_version"] == APP_VERSION
    assert data["model_version"] == MODEL_VERSION
    assert data["dataset_version"] == DATASET_VERSION
    assert "timestamp" in data


def test_version_endpoint(client):
    """Verify that /version returns full application and build metadata."""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "AgriRisk Kenya"
    assert data["app_version"] == APP_VERSION
    assert data["model_version"] == MODEL_VERSION
    assert data["dataset_version"] == DATASET_VERSION


def test_risk_latest_endpoint(client):
    """Verify that /api/v1/risk/latest returns structured risk scores across monitored counties."""
    response = client.get("/api/v1/risk/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["counties_monitored"] > 0
    assert len(data["scores"]) > 0
    first_score = data["scores"][0]
    assert "county" in first_score
    assert "calibrated_probability" in first_score
    assert "confidence_interval" in first_score
    assert first_score["risk_band"] in ("Low", "Moderate", "Elevated", "High")
    assert "disclaimer" in first_score


def test_county_risk_endpoint(client):
    """Verify that /api/v1/risk/{county} returns correct score for valid county and 404 for invalid."""
    # Valid county
    response = client.get("/api/v1/risk/Turkana")
    assert response.status_code == 200
    data = response.json()
    assert data["county"].lower() == "turkana"

    # Non-existent county
    invalid_resp = client.get("/api/v1/risk/Atlantis")
    assert invalid_resp.status_code == 404


def test_county_forecast_endpoint(client):
    """Verify multi-horizon forecasts for a county."""
    response = client.get("/api/v1/forecast/Turkana")
    assert response.status_code == 200
    data = response.json()
    assert data["county"].lower() == "turkana"
    assert len(data["forecasts"]) == 3
    assert data["forecasts"][0]["horizon_months"] == 1
    assert data["forecasts"][1]["horizon_months"] == 2
    assert data["forecasts"][2]["horizon_months"] == 3


def test_data_status_endpoint(client):
    """Verify data status reporting across multi-source streams."""
    response = client.get("/api/v1/data-status")
    assert response.status_code == 200
    data = response.json()
    assert "Current" in data["overall_status"]
    assert "CHIRPS" in data["climate_latest"]
    assert "MODIS" in data["vegetation_latest"]
    assert "WFP" in data["market_latest"]


def test_model_artifact_manager_loading_and_validation():
    """Verify that ModelArtifactManager successfully validates feature schema."""
    mgr = ModelArtifactManager()
    mgr.load()
    assert mgr._is_loaded is True
    assert mgr.schema is not None
    assert "expected_features" in mgr.schema

    # Create dummy dataframe with all expected features
    features = mgr.schema["expected_features"]
    dummy_df = pd.DataFrame({f: [0.5] for f in features})
    is_valid, missing = mgr.validate_features(dummy_df)
    assert is_valid is True
    assert len(missing) == 0

    # Incomplete dataframe
    incomplete_df = pd.DataFrame({"random_col": [1.0]})
    is_valid_bad, missing_bad = mgr.validate_features(incomplete_df)
    assert is_valid_bad is False
    assert len(missing_bad) > 0
