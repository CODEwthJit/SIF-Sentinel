"""
Pydantic Schemas for Authentication & User Entities
Phase 9.4 — SIH26165
"""

from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Full name or display name of the user.")
    email: EmailStr = Field(..., description="Valid work/personal email address.")
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password (min 8 characters).")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Name cannot be empty or whitespace-only.")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Registered account email address.")
    password: str = Field(..., description="Account password.")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

