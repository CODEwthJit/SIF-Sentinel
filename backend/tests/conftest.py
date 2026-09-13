"""
Pytest Configuration & Fixtures for Backend Tests
Phase 9.1 — SIH26165
"""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure root is in sys.path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backend.app.db.database import Base, get_db
from backend.app.main import app

# In-memory SQLite specifically configured for complete test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Creates isolated in-memory tables per test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with isolated database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Creates a standard test user in the isolated database."""
    from backend.app.db.models import User
    from backend.app.core.security import hash_password

    user = User(
        name="Test User A",
        email="user_a@example.com",
        password_hash=hash_password("Password123!"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Generates valid JWT bearer authorization headers for test_user."""
    from backend.app.core.security import create_access_token

    token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user_b(db_session):
    """Creates a second distinct user for multi-tenant isolation testing."""
    from backend.app.db.models import User
    from backend.app.core.security import hash_password

    user = User(
        name="Test User B",
        email="user_b@example.com",
        password_hash=hash_password("Password456!"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def user_b_headers(user_b):
    """Generates valid JWT bearer authorization headers for user_b."""
    from backend.app.core.security import create_access_token

    token = create_access_token(data={"sub": user_b.email, "user_id": user_b.id})
    return {"Authorization": f"Bearer {token}"}

