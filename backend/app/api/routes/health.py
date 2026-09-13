"""
Health Check Endpoint
Phase 9.1 — SIH26165
"""

from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Returns basic service health status and engine specifications."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "pipeline": "2.3.0-BUGFIX-FROZEN",
        "ml_model": "TF-IDF + Logistic Regression (tau=0.59)",
        "reconciliation": "Categorical Matrix Triage"
    }

