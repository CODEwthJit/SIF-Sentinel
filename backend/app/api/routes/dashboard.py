"""
Dashboard Analytics Endpoints
Phase 9.1 — SIH26165
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import User
from backend.app.core.security import get_current_user
from backend.app.schemas.dashboard import DashboardStatsResponse, DashboardRecentResponse
from backend.app.services.analysis_service import AnalysisService

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/dashboard/stats",
    response_model=DashboardStatsResponse,
    summary="Get SIF Dashboard Summary Statistics",
    description="Returns aggregate statistics computed strictly from persisted database analyses for the authenticated user."
)
def get_dashboard_stats_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Computes and returns aggregate application statistics scoped to current user."""
    return AnalysisService.get_dashboard_stats(db=db, user_id=current_user.id)


@router.get(
    "/dashboard/recent",
    response_model=DashboardRecentResponse,
    summary="Get Recent Analyses for Dashboard Feed",
    description="Returns recent analysis triage items for real-time EHS dashboard feeds for the authenticated user."
)
def get_dashboard_recent_endpoint(
    limit: int = Query(10, ge=1, le=50, description="Number of recent analyses to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves recent analyses for dashboard activity stream scoped to current user."""
    return AnalysisService.get_dashboard_recent(db=db, user_id=current_user.id, limit=limit)

