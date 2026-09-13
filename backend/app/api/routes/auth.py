"""
Authentication Endpoints
Phase 9.4 — SIH26165
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import User
from backend.app.schemas.auth import UserRegister, UserLogin, UserOut, Token
from backend.app.services.auth_service import AuthService
from backend.app.core.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Creates a new user account with secure password hashing and returns an authenticated JWT token."
)
def register_endpoint(
    payload: UserRegister,
    db: Session = Depends(get_db)
):
    """Registers new user account and returns access token."""
    user, token = AuthService.register_user(db=db, payload=payload)
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User and Issue JWT",
    description="Authenticates credentials and returns a signed JWT access token. Generic 401 error returned on failure."
)
def login_endpoint(
    payload: UserLogin,
    db: Session = Depends(get_db)
):
    """Authenticates credentials and returns access token."""
    user, token = AuthService.authenticate_user(db=db, payload=payload)
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User Profile",
    description="Returns profile information for the authenticated token bearer. Never leaks password hashes."
)
def get_me_endpoint(
    current_user: User = Depends(get_current_user)
):
    """Returns safe user information for the authenticated user."""
    return UserOut.model_validate(current_user)

