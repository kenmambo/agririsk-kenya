"""Unit tests for FastAPI endpoints (Health and Counties catalog)."""


def test_health_endpoint(test_client):
    """Verify that /health responds with 200 and healthy status."""
    response = test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_status"] == "connected"
    assert "AgriRisk Kenya" in data["app_name"]
    assert "timestamp" in data


def test_api_v1_health_prefix(test_client):
    """Verify /api/v1/health responds with healthy payload."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_list_counties(test_client):
    """Verify listing all 47 counties via API."""
    response = test_client.get("/api/v1/counties")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 47
    assert data[0]["code"] == "001"


def test_api_filter_counties_by_asal(test_client):
    """Verify filtering counties by ASAL category."""
    response = test_client.get("/api/v1/counties?asal_category=Arid")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(c["asal_category"] == "Arid" for c in data)


def test_api_get_single_county(test_client):
    """Verify fetching a specific county by code."""
    response = test_client.get("/api/v1/counties/023")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Turkana"
    assert data["code"] == "023"


def test_api_get_single_county_not_found(test_client):
    """Verify 404 response for non-existent county."""
    response = test_client.get("/api/v1/counties/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
