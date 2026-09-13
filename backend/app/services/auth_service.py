"""
Authentication Service Layer
Phase 9.4 — SIH26165

Handles:
1. User registration with email uniqueness validation and password hashing.
2. User credential verification and JWT token issuance.
3. Strict protection against password leakage in logs or responses.
"""

from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.models import User
from backend.app.schemas.auth import UserRegister, UserLogin
from backend.app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    """Encapsulates user registration, verification, and token issuance."""

    @staticmethod
    def register_user(db: Session, payload: UserRegister) -> Tuple[User, str]:
        """
        Registers a new user with bcrypt-hashed password and returns (user, token).
        Raises HTTP 409 if email already exists.
        """
        normalized_email = payload.email.strip().lower()

        # Check for existing account
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists."
            )

        # Hash password securely
        pwd_hash = hash_password(payload.password)

        # Create and persist user entity
        user = User(
            name=payload.name.strip(),
            email=normalized_email,
            password_hash=pwd_hash,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Issue JWT access token for immediate session establishment
        token = create_access_token(data={"sub": user.email, "user_id": user.id})
        return user, token

    @staticmethod
    def authenticate_user(db: Session, payload: UserLogin) -> Tuple[User, str]:
        """
        Authenticates user credentials and returns (user, token).
        Raises generic HTTP 401 on invalid email or password without leaking account existence.
        """
        normalized_email = payload.email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()

        # Generic authentication failure message to prevent username enumeration
        generic_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

        if not user:
            raise generic_error

        if not verify_password(payload.password, user.password_hash):
            raise generic_error

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated. Please contact an administrator.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Issue JWT access token
        token = create_access_token(data={"sub": user.email, "user_id": user.id})
        return user, token

