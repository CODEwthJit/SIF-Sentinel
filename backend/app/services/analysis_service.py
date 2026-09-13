"""
SIF Analysis Service Layer
Phase 9.1 — SIH26165

Responsible for:
1. Delegating inference strictly to the frozen pipeline: `sif_pipeline.analyze_report()`
2. Mapping pipeline output to SQLAlchemy models
3. Persisting reports and analyses in the database
4. Assembling strongly-typed Pydantic response models
5. Providing historical report and dashboard query operations

Invariant:
Routes never execute business logic; all intelligence remains in the frozen core.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.sif_pipeline import analyze_report
from backend.app.db.models import Report, Analysis
from backend.app.schemas.reports import ReportOut
from backend.app.schemas.analysis import (
    AnalysisResponse,
    ReportDetailResponse,
    MLEvidenceSchema,
    RuleEvidenceSchema,
    ReconciliationSchema,
    LexicalEvidenceItem
)
from backend.app.schemas.dashboard import (
    DashboardStatsResponse,
    DashboardRecentResponse,
    RecentAnalysisItem
)


class AnalysisService:
    """Service encapsulating SIF analysis pipeline execution and database operations."""

    @staticmethod
    def analyze_and_persist(db: Session, narrative: str, user_id: Optional[int] = None) -> AnalysisResponse:
        """
        Executes the frozen SIF pipeline against the narrative, persists report
        and analysis records associated with user_id, and returns a typed AnalysisResponse.
        """
        # 1. Execute frozen intelligence pipeline
        pipeline_res = analyze_report(narrative)

        # 2. Persist Report entity
        clean_narrative = pipeline_res["narrative"]
        report_record = Report(narrative=clean_narrative, user_id=user_id)
        db.add(report_record)
        db.flush()  # Populates report_record.id

        # 3. Extract evidence blocks
        ml_block = pipeline_res["ml"]
        rule_block = pipeline_res["rule"]
        recon_block = pipeline_res["reconciliation"]

        # 4. Persist Analysis entity
        analysis_record = Analysis(
            report_id=report_record.id,
            ml_label=ml_block["label"],
            ml_score=float(ml_block["score"]),
            ml_threshold=float(ml_block.get("threshold", 0.59)),
            decision_rationale=ml_block.get("decision_rationale"),
            positive_evidence=ml_block.get("positive_evidence", []),
            negative_evidence=ml_block.get("negative_evidence", []),
            rule_label=rule_block["label"],
            rule_reason_code=rule_block.get("reason_code"),
            rule_energy=rule_block.get("energy"),
            rule_barrier=rule_block.get("barrier"),
            rule_exposure=rule_block.get("human_exposure"),
            rule_evidence_sufficiency=rule_block.get("evidence_sufficiency"),
            precursor_type=rule_block.get("precursor_type"),
            confidence=rule_block.get("confidence"),
            reconciliation_status=recon_block["status"],
            reconciliation_priority=recon_block["priority"],
            human_review_required=bool(recon_block["review_required"]),
            discrepancy=bool(recon_block["discrepancy"]),
            explanation=recon_block.get("explanation")
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(report_record)
        db.refresh(analysis_record)

        # 5. Format and return typed response
        return AnalysisService._format_analysis_response(report_record, analysis_record)

    @staticmethod
    def get_reports(db: Session, user_id: Optional[int] = None, limit: int = 20, offset: int = 0) -> List[ReportOut]:
        """Returns list of recent reports scoped to user_id if provided."""
        query = db.query(Report)
        if user_id is not None:
            query = query.filter(Report.user_id == user_id)

        records = (
            query
            .order_by(Report.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [ReportOut.model_validate(r) for r in records]

    @staticmethod
    def get_report_by_id(db: Session, report_id: int, user_id: Optional[int] = None) -> Optional[ReportDetailResponse]:
        """Returns full report detail and its latest analysis, scoped to user_id if provided."""
        query = db.query(Report).filter(Report.id == report_id)
        if user_id is not None:
            query = query.filter(Report.user_id == user_id)

        report = query.first()
        if not report:
            return None

        latest_analysis_obj = (
            db.query(Analysis)
            .filter(Analysis.report_id == report_id)
            .order_by(Analysis.id.desc())
            .first()
        )

        total_analyses = db.query(Analysis).filter(Analysis.report_id == report_id).count()

        latest_resp = None
        if latest_analysis_obj:
            latest_resp = AnalysisService._format_analysis_response(report, latest_analysis_obj)

        return ReportDetailResponse(
            report=ReportOut.model_validate(report),
            latest_analysis=latest_resp,
            total_analyses=total_analyses
        )

    @staticmethod
    def get_dashboard_stats(db: Session, user_id: Optional[int] = None) -> DashboardStatsResponse:
        """Aggregates real statistics from persisted database analyses scoped to user_id."""
        report_q = db.query(Report)
        analysis_q = db.query(Analysis).join(Report, Analysis.report_id == Report.id)

        if user_id is not None:
            report_q = report_q.filter(Report.user_id == user_id)
            analysis_q = analysis_q.filter(Report.user_id == user_id)

        total_reports = report_q.count()
        total_analyses = analysis_q.count()

        if total_analyses == 0:
            return DashboardStatsResponse(
                total_reports=total_reports,
                total_analyses=0
            )

        # Aggregate counts by categorical status
        status_q = db.query(Analysis.reconciliation_status, func.count(Analysis.id)).join(Report, Analysis.report_id == Report.id)
        if user_id is not None:
            status_q = status_q.filter(Report.user_id == user_id)
        status_rows = status_q.group_by(Analysis.reconciliation_status).all()
        status_dist = {status: count for status, count in status_rows}

        # Aggregate counts by priority
        priority_q = db.query(Analysis.reconciliation_priority, func.count(Analysis.id)).join(Report, Analysis.report_id == Report.id)
        if user_id is not None:
            priority_q = priority_q.filter(Report.user_id == user_id)
        priority_rows = priority_q.group_by(Analysis.reconciliation_priority).all()
        priority_dist = {priority: count for priority, count in priority_rows}

        # Aggregate counts by reason code
        reason_q = (
            db.query(Analysis.rule_reason_code, func.count(Analysis.id))
            .join(Report, Analysis.report_id == Report.id)
            .filter(Analysis.rule_reason_code.isnot(None))
        )
        if user_id is not None:
            reason_q = reason_q.filter(Report.user_id == user_id)
        reason_rows = (
            reason_q
            .group_by(Analysis.rule_reason_code)
            .order_by(func.count(Analysis.id).desc())
            .limit(10)
            .all()
        )
        reason_dist = {reason: count for reason, count in reason_rows if reason}

        # Aggregate counts by hazard energy
        energy_q = (
            db.query(Analysis.rule_energy, func.count(Analysis.id))
            .join(Report, Analysis.report_id == Report.id)
            .filter(Analysis.rule_energy.isnot(None))
        )
        if user_id is not None:
            energy_q = energy_q.filter(Report.user_id == user_id)
        energy_rows = (
            energy_q
            .group_by(Analysis.rule_energy)
            .order_by(func.count(Analysis.id).desc())
            .limit(10)
            .all()
        )
        energy_dist = {energy: count for energy, count in energy_rows if energy}

        consensus_sif = status_dist.get("CONSENSUS_SIF", 0)
        consensus_non_sif = status_dist.get("CONSENSUS_NON_SIF", 0)
        discrepancy_count = sum(
            count for status, count in status_dist.items()
            if status not in ["CONSENSUS_SIF", "CONSENSUS_NON_SIF"]
        )

        return DashboardStatsResponse(
            total_reports=total_reports,
            total_analyses=total_analyses,
            consensus_sif_count=consensus_sif,
            consensus_non_sif_count=consensus_non_sif,
            discrepancy_count=discrepancy_count,
            high_priority_count=priority_dist.get("HIGH", 0),
            medium_priority_count=priority_dist.get("MEDIUM", 0),
            low_priority_count=priority_dist.get("LOW", 0),
            reconciliation_status_distribution=status_dist,
            review_priority_distribution=priority_dist,
            rule_reason_code_distribution=reason_dist,
            hazard_energy_distribution=energy_dist
        )

    @staticmethod
    def get_dashboard_recent(db: Session, user_id: Optional[int] = None, limit: int = 10) -> DashboardRecentResponse:
        """Returns recent analyses formatted for dashboard feed scoped to user_id."""
        query = (
            db.query(Analysis, Report)
            .join(Report, Analysis.report_id == Report.id)
        )
        if user_id is not None:
            query = query.filter(Report.user_id == user_id)

        records = (
            query
            .order_by(Analysis.created_at.desc())
            .limit(limit)
            .all()
        )

        recent_items = []
        for analysis, report in records:
            narrative_preview = (
                report.narrative[:90] + "..." if len(report.narrative) > 90 else report.narrative
            )
            recent_items.append(
                RecentAnalysisItem(
                    report_id=report.id,
                    narrative_preview=narrative_preview,
                    ml_label=analysis.ml_label,
                    ml_score=analysis.ml_score,
                    rule_label=analysis.rule_label,
                    reconciliation_status=analysis.reconciliation_status,
                    review_priority=analysis.reconciliation_priority,
                    human_review_required=analysis.human_review_required,
                    created_at=analysis.created_at
                )
            )

        return DashboardRecentResponse(
            total_returned=len(recent_items),
            recent_analyses=recent_items
        )

    @staticmethod
    def _format_analysis_response(report: Report, analysis: Analysis) -> AnalysisResponse:
        """Helper mapping ORM entities into AnalysisResponse schema."""
        pos_ev = [
            LexicalEvidenceItem(**item) for item in (analysis.positive_evidence or [])
            if isinstance(item, dict)
        ]
        neg_ev = [
            LexicalEvidenceItem(**item) for item in (analysis.negative_evidence or [])
            if isinstance(item, dict)
        ]

        return AnalysisResponse(
            report=ReportOut.model_validate(report),
            ml=MLEvidenceSchema(
                label=analysis.ml_label,
                score=analysis.ml_score,
                threshold=analysis.ml_threshold,
                positive_evidence=pos_ev,
                negative_evidence=neg_ev,
                decision_rationale=analysis.decision_rationale
            ),
            rule=RuleEvidenceSchema(
                label=analysis.rule_label,
                reason_code=analysis.rule_reason_code,
                controlling_hazard_energy=analysis.rule_energy,
                barrier_state=analysis.rule_barrier,
                human_exposure=analysis.rule_exposure,
                evidence_sufficiency=analysis.rule_evidence_sufficiency,
                precursor_type=analysis.precursor_type,
                confidence=analysis.confidence
            ),
            reconciliation=ReconciliationSchema(
                status=analysis.reconciliation_status,
                priority=analysis.reconciliation_priority,
                discrepancy=analysis.discrepancy,
                review_required=analysis.human_review_required,
                explanation=analysis.explanation
            )
        )
