"""
Reports & SIF Analysis Endpoints
Phase 9.1 — SIH26165
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import User
from backend.app.schemas.reports import ReportCreate, ReportOut
from backend.app.schemas.analysis import AnalysisResponse, ReportDetailResponse
from backend.app.services.analysis_service import AnalysisService
from backend.app.core.security import get_current_user

router = APIRouter(tags=["Reports & Analysis"])


@router.post(
    "/reports/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Narrative for SIF Analysis",
    description=(
        "Submits an incident narrative to the frozen SIF pipeline, executing NLP normalization, "
        "ML inference, V2.3 deterministic rule evaluation, and categorical reconciliation. "
        "Persists the report and analysis results associated with the authenticated user."
    )
)
def analyze_report_endpoint(
    payload: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Executes frozen SIF analysis and persists results for current_user."""
    try:
        response = AnalysisService.analyze_and_persist(
            db=db,
            narrative=payload.narrative,
            user_id=current_user.id
        )
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline processing failed: {str(exc)}"
        )


@router.get(
    "/reports",
    response_model=List[ReportOut],
    summary="List Analyzed Reports History",
    description="Returns a paginated list of previously analyzed incident reports belonging to current user."
)
def list_reports(
    limit: int = Query(20, ge=1, le=100, description="Number of reports to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves paginated history of reports for current_user."""
    return AnalysisService.get_reports(db=db, user_id=current_user.id, limit=limit, offset=offset)


@router.get(
    "/reports/{report_id}",
    response_model=ReportDetailResponse,
    summary="Get Report Detail and Latest Analysis",
    description="Retrieves a specific incident report and its complete SIF analysis breakdown by ID for current user."
)
def get_report_detail(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves report by ID for current_user. Returns 404 if not found or unauthorized."""
    report_detail = AnalysisService.get_report_by_id(db=db, report_id=report_id, user_id=current_user.id)
    if not report_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found."
        )
    return report_detail

