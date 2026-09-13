"""
Backend Dashboard Analytics Endpoint Tests
Phase 9.1 — SIH26165
"""


def test_dashboard_unauthenticated_fails(client):
    """Verifies that unauthenticated requests to dashboard endpoints return 401 Unauthorized."""
    res_stats = client.get("/api/v1/dashboard/stats")
    assert res_stats.status_code == 401

    res_recent = client.get("/api/v1/dashboard/recent")
    assert res_recent.status_code == 401


def test_dashboard_stats_empty(client, auth_headers):
    """Test 8a: Dashboard stats on empty database returns zeroed counts without failure."""
    response = client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_reports"] == 0
    assert data["total_analyses"] == 0
    assert data["consensus_sif_count"] == 0


def test_dashboard_stats_with_data(client, auth_headers):
    """Test 8b: Dashboard stats computes real persisted counts and category distributions."""
    # 1. Clear SIF incident
    client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "An employee fell 28 feet from a scaffold after the scaffold collapsed."},
        headers=auth_headers
    )
    # 2. Clear Non-SIF incident
    client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "An employee slipped and fell on ice on the sidewalk outside the entrance, bruising his knee."},
        headers=auth_headers
    )
    # 3. Disagreement case
    client.post(
        "/api/v1/reports/analyze",
        json={
            "narrative": (
                "An employee was using a wrench to remove snow that was blocking the magic carpet conveyor belt machine. "
                "As soon as the snow was released, the conveyor started going again and grabbed the wrench. "
                "When the employee tried to grab the tool, she was trapped under the conveyor belt bar, breaking her right humerus."
            )
        },
        headers=auth_headers
    )

    response = client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_reports"] == 3
    assert data["total_analyses"] == 3
    assert data["consensus_sif_count"] == 1
    assert data["consensus_non_sif_count"] == 1
    assert data["discrepancy_count"] == 1
    assert data["high_priority_count"] >= 2  # SIF + Disagreement are both HIGH priority

    # Verify distributions
    assert "CONSENSUS_SIF" in data["reconciliation_status_distribution"]
    assert "CONSENSUS_NON_SIF" in data["reconciliation_status_distribution"]
    assert "DIRECT_DISAGREEMENT" in data["reconciliation_status_distribution"]


def test_dashboard_recent_analyses(client, auth_headers):
    """Test 8c: Returns recent analyses with previews."""
    client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "Worker sustained a gravitational fall from 20 feet above ground."},
        headers=auth_headers
    )

    response = client.get("/api/v1/dashboard/recent?limit=5", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_returned"] >= 1
    recent = data["recent_analyses"][0]
    assert "gravitational fall" in recent["narrative_preview"].lower()
    assert recent["reconciliation_status"] == "CONSENSUS_SIF"
    assert recent["review_priority"] == "HIGH"

