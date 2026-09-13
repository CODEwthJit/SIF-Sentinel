"""
Backend Reports & SIF Analysis Endpoint Tests
Phase 9.1 — SIH26165
"""

from unittest.mock import patch
from backend.app.db.models import Report, Analysis


def test_unauthenticated_requests_fail(client):
    """Verifies that unauthenticated requests to protected endpoints return 401 Unauthorized."""
    res_analyze = client.post("/api/v1/reports/analyze", json={"narrative": "Some narrative"})
    assert res_analyze.status_code == 401

    res_history = client.get("/api/v1/reports")
    assert res_history.status_code == 401

    res_detail = client.get("/api/v1/reports/1")
    assert res_detail.status_code == 401


def test_empty_narrative_rejection(client, auth_headers):
    """Test 2: Rejects empty or whitespace-only narratives with HTTP 422."""
    # Completely empty
    res_empty = client.post("/api/v1/reports/analyze", json={"narrative": ""}, headers=auth_headers)
    assert res_empty.status_code == 422

    # Whitespace only
    res_ws = client.post("/api/v1/reports/analyze", json={"narrative": "    "}, headers=auth_headers)
    assert res_ws.status_code == 422

    # Missing field
    res_missing = client.post("/api/v1/reports/analyze", json={}, headers=auth_headers)
    assert res_missing.status_code == 422


def test_valid_analysis_request_and_persistence(client, db_session, auth_headers, test_user):
    """Test 3 & 5: Valid analysis request executes pipeline, persists records, and returns typed response."""
    payload = {
        "narrative": "An employee fell 28 feet from a scaffold after the scaffold collapsed."
    }
    response = client.post("/api/v1/reports/analyze", json=payload, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert "report" in data
    assert "ml" in data
    assert "rule" in data
    assert "reconciliation" in data

    # Verify Report block
    report_id = data["report"]["id"]
    assert report_id > 0
    assert "fell 28 feet" in data["report"]["narrative"]

    # Verify ML block
    assert data["ml"]["label"] == "YES"
    assert data["ml"]["score"] >= 0.59
    assert data["ml"]["threshold"] == 0.59

    # Verify Rule block
    assert data["rule"]["label"] == "YES"
    assert data["rule"]["reason_code"] == "GRAVITATIONAL_EXPOSURE"
    assert data["rule"]["controlling_hazard_energy"] == "GRAVITATIONAL"

    # Verify Reconciliation block
    assert data["reconciliation"]["status"] == "CONSENSUS_SIF"
    assert data["reconciliation"]["priority"] == "HIGH"
    assert data["reconciliation"]["discrepancy"] is False
    assert data["reconciliation"]["review_required"] is False

    # Assert Persistence in Database with User Ownership
    db_report = db_session.query(Report).filter(Report.id == report_id).first()
    assert db_report is not None
    assert "fell 28 feet" in db_report.narrative
    assert db_report.user_id == test_user.id

    db_analysis = db_session.query(Analysis).filter(Analysis.report_id == report_id).first()
    assert db_analysis is not None
    assert db_analysis.reconciliation_status == "CONSENSUS_SIF"
    assert db_analysis.ml_label == "YES"


def test_pipeline_failure_handling(client, auth_headers):
    """Test 4: Handles pipeline exceptions gracefully without leaking internal stack traces."""
    with patch("backend.app.services.analysis_service.analyze_report") as mock_pipeline:
        mock_pipeline.side_effect = RuntimeError("Simulated internal ML tensor error")

        payload = {"narrative": "Some incident narrative"}
        response = client.post("/api/v1/reports/analyze", json=payload, headers=auth_headers)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Simulated internal ML tensor error" in data["detail"]
        # Ensure no raw Python traceback object is dumped in the response
        assert "Traceback (most recent call last)" not in response.text


def test_report_history(client, auth_headers):
    """Test 6: Returns chronological list of analyzed reports."""
    # Analyze two distinct incidents
    client.post("/api/v1/reports/analyze", json={"narrative": "First report narrative for history test."}, headers=auth_headers)
    client.post("/api/v1/reports/analyze", json={"narrative": "Second report narrative for history test."}, headers=auth_headers)

    response = client.get("/api/v1/reports?limit=10", headers=auth_headers)
    assert response.status_code == 200
    reports_list = response.json()
    assert len(reports_list) >= 2
    # Recency check: most recent is first
    assert "Second report narrative" in reports_list[0]["narrative"]


def test_report_detail(client, auth_headers):
    """Test 7: Returns complete report detail and analysis breakdown by ID."""
    create_res = client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "An employee slipped and fell on ice on the sidewalk outside the entrance, bruising his knee."},
        headers=auth_headers
    )
    report_id = create_res.json()["report"]["id"]

    # Query detail
    detail_res = client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    data = detail_res.json()

    assert data["report"]["id"] == report_id
    assert data["total_analyses"] == 1
    assert data["latest_analysis"] is not None
    assert data["latest_analysis"]["reconciliation"]["status"] == "CONSENSUS_NON_SIF"
    assert data["latest_analysis"]["rule"]["reason_code"] == "LOW_ENERGY_SAME_LEVEL_FALL"


def test_report_detail_not_found(client, auth_headers):
    """Test 7b: Returns 404 for non-existent report ID."""
    response = client.get("/api/v1/reports/999999", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

