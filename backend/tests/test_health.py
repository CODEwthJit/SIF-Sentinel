"""
Backend Health Endpoint Tests
Phase 9.1 — SIH26165
"""


def test_health_endpoint(client):
    """Test 1: Health endpoint returns status ok and system metadata."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "SIH26165" in data["service"]
    assert data["pipeline"] == "2.3.0-BUGFIX-FROZEN"
    assert "0.59" in data["ml_model"]


def test_root_endpoint(client):
    """Test root redirect / info endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["docs"] == "/docs"

