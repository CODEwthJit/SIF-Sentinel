"""
Pydantic Schemas for Dashboard Analytics
Phase 9.1 — SIH26165
"""

from typing import Dict, List
from datetime import datetime
from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    total_reports: int = Field(..., description="Total unique incident reports recorded.")
    total_analyses: int = Field(..., description="Total analysis pipeline evaluations executed.")
    consensus_sif_count: int = Field(0, description="Count of full Consensus SIF incidents.")
    consensus_non_sif_count: int = Field(0, description="Count of full Consensus Non-SIF incidents.")
    discrepancy_count: int = Field(0, description="Count of reports where ML and Rule channels diverge.")
    high_priority_count: int = Field(0, description="Count of reports requiring HIGH priority review.")
    medium_priority_count: int = Field(0, description="Count of reports requiring MEDIUM priority review.")
    low_priority_count: int = Field(0, description="Count of reports requiring LOW priority review.")
    reconciliation_status_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Frequencies by categorical status."
    )
    review_priority_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Frequencies by review priority tier."
    )
    rule_reason_code_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Frequencies by V2.3 rule reason codes."
    )
    hazard_energy_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Frequencies by controlling hazard energy mechanisms."
    )


class RecentAnalysisItem(BaseModel):
    report_id: int
    narrative_preview: str
    ml_label: str
    ml_score: float
    rule_label: str
    reconciliation_status: str
    review_priority: str
    human_review_required: bool
    created_at: datetime


class DashboardRecentResponse(BaseModel):
    total_returned: int
    recent_analyses: List[RecentAnalysisItem]

