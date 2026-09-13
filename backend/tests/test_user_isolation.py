"""
User Isolation & Multi-Tenancy Tests
Phase 9.4 — SIH26165

Verifies strict user boundary separation across:
1. Report submission and ownership assignment.
2. Chronological report history scoping.
3. Direct report detail lookup (cross-user access returns HTTP 404).
4. Dashboard summary aggregate statistics scoping.
5. Dashboard recent analysis activity feed scoping.
"""


def test_user_ownership_and_history_isolation(client, auth_headers, user_b_headers):
    """Verifies that each user only sees their own reports in history."""
    # User A submits a report
    res_a = client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "User A incident: Technician fell from scaffolding while inspecting tank."},
        headers=auth_headers
    )
    assert res_a.status_code == 201
    report_a_id = res_a.json()["report"]["id"]

    # User B submits a report
    res_b = client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "User B incident: Operator suffered acid chemical burn during line transfer."},
        headers=user_b_headers
    )
    assert res_b.status_code == 201
    report_b_id = res_b.json()["report"]["id"]

    # User A views history -> must ONLY contain Report A
    history_a = client.get("/api/v1/reports", headers=auth_headers).json()
    ids_a = [r["id"] for r in history_a]
    assert report_a_id in ids_a
    assert report_b_id not in ids_a

    # User B views history -> must ONLY contain Report B
    history_b = client.get("/api/v1/reports", headers=user_b_headers).json()
    ids_b = [r["id"] for r in history_b]
    assert report_b_id in ids_b
    assert report_a_id not in ids_b


def test_cross_user_report_access_returns_404(client, auth_headers, user_b_headers):
    """
    Verifies that accessing another user's report returns HTTP 404 Not Found,
    preventing any report existence disclosure.
    """
    # User A creates a report
    res_a = client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "Confidential incident narrative belonging strictly to User A."},
        headers=auth_headers
    )
    report_a_id = res_a.json()["report"]["id"]

    # User B attempts to view User A's report by ID
    res_b_attempt = client.get(f"/api/v1/reports/{report_a_id}", headers=user_b_headers)
    assert res_b_attempt.status_code == 404
    assert "not found" in res_b_attempt.json()["detail"].lower()

    # User A can view their own report
    res_a_view = client.get(f"/api/v1/reports/{report_a_id}", headers=auth_headers)
    assert res_a_view.status_code == 200
    assert res_a_view.json()["report"]["id"] == report_a_id


def test_dashboard_stats_and_recent_isolation(client, auth_headers, user_b_headers):
    """Verifies that dashboard stats and recent analysis feeds are strictly partitioned."""
    # User A submits 2 reports: 1 SIF, 1 Non-SIF
    client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "Employee fell 30 feet from communication tower."},
        headers=auth_headers
    )
    client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "An employee slipped and fell on ice on the sidewalk outside the entrance, bruising his knee."},
        headers=auth_headers
    )

    # User B submits 1 report: 1 SIF
    client.post(
        "/api/v1/reports/analyze",
        json={"narrative": "High voltage electrical flash caused arc flash burn to electrician."},
        headers=user_b_headers
    )

    # Verify User A dashboard stats
    stats_a = client.get("/api/v1/dashboard/stats", headers=auth_headers).json()
    assert stats_a["total_reports"] == 2
    assert stats_a["total_analyses"] == 2
    assert stats_a["consensus_sif_count"] == 1
    assert stats_a["consensus_non_sif_count"] == 1

    # Verify User B dashboard stats
    stats_b = client.get("/api/v1/dashboard/stats", headers=user_b_headers).json()
    assert stats_b["total_reports"] == 1
    assert stats_b["total_analyses"] == 1
    assert stats_b["consensus_sif_count"] == 1
    assert stats_b["consensus_non_sif_count"] == 0

    # Verify User A recent feed contains only User A's reports
    recent_a = client.get("/api/v1/dashboard/recent", headers=auth_headers).json()
    assert recent_a["total_returned"] == 2
    for item in recent_a["recent_analyses"]:
        assert "arc flash" not in item["narrative_preview"].lower()

    # Verify User B recent feed contains only User B's reports
    recent_b = client.get("/api/v1/dashboard/recent", headers=user_b_headers).json()
    assert recent_b["total_returned"] == 1
    assert "arc flash" in recent_b["recent_analyses"][0]["narrative_preview"].lower()
