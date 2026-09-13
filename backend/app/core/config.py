"""
Configuration Module for SIF Backend
Phase 9.1 — SIH26165
"""

import os
from typing import List


class Settings:
    PROJECT_NAME: str = "SIH26165 — SIF Precursor Detection API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database: Default to SQLite for zero-config local dev & tests; configurable for PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./sif_backend.db"
    )

    # CORS origins configuration
    _cors_raw: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"
    )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        if isinstance(self._cors_raw, list):
            return self._cors_raw
        return [origin.strip() for origin in self._cors_raw.split(",") if origin.strip()]

    # JWT Authentication Configuration
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "dev_jwt_secret_key_sih26165_32chars_minimum_length"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


settings = Settings()

