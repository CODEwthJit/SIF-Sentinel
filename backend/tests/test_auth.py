"""
Authentication Service & Endpoint Tests
Phase 9.4 — SIH26165
"""

from backend.app.db.models import User
from backend.app.core.security import verify_password


def test_user_registration_success(client, db_session):
    """Verifies successful user registration with hashed password and token issuance."""
    payload = {
        "name": "Alice Engineer",
        "email": "alice@company.org",
        "password": "SecurePassword123!"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "alice@company.org"
    assert data["user"]["name"] == "Alice Engineer"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    # Verify database persistence & password hashing
    persisted_user = db_session.query(User).filter(User.email == "alice@company.org").first()
    assert persisted_user is not None
    assert persisted_user.password_hash != "SecurePassword123!"
    assert persisted_user.password_hash.startswith("$2b$") or persisted_user.password_hash.startswith("$2a$")
    assert verify_password("SecurePassword123!", persisted_user.password_hash) is True


def test_user_registration_duplicate_email_rejected(client):
    """Verifies duplicate email registration fails with HTTP 409 Conflict."""
    payload = {
        "name": "Bob Builder",
        "email": "bob@company.org",
        "password": "Password456!"
    }
    # Initial registration
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email (case-insensitive check)
    payload_dup = {
        "name": "Bob Duplicate",
        "email": "BOB@COMPANY.ORG",
        "password": "OtherPassword789!"
    }
    res2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


def test_user_login_success(client, test_user):
    """Verifies valid credentials authenticate and return a valid JWT token."""
    payload = {
        "email": test_user.email,
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == test_user.email
    assert data["user"]["id"] == test_user.id


def test_user_login_invalid_password_returns_401(client, test_user):
    """Verifies incorrect password returns generic 401 Unauthorized without enumeration."""
    payload = {
        "email": test_user.email,
        "password": "WrongPassword999!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid email address or password" in response.json()["detail"].lower()


def test_user_login_nonexistent_email_returns_401(client):
    """Verifies non-existent email returns generic 401 Unauthorized identically."""
    payload = {
        "email": "ghost@company.org",
        "password": "SomePassword123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid email address or password" in response.json()["detail"].lower()


def test_get_current_user_me_endpoint(client, test_user, auth_headers):
    """Verifies GET /api/v1/auth/me returns authenticated user identity."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name


def test_get_current_user_me_unauthorized(client):
    """Verifies GET /api/v1/auth/me fails when missing token or with invalid token."""
    # Missing token
    res_no_token = client.get("/api/v1/auth/me")
    assert res_no_token.status_code == 401

    # Invalid token
    res_bad_token = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad-token-12345"})
    assert res_bad_token.status_code == 401

