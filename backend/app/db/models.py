"""
SQLAlchemy Relational Models
Phase 9.1 — SIH26165

Tables:
- users
- reports
- analyses

Strict Invariants:
- Zero storage of prohibited outcome metadata (hospitalized, amputation, fatal).
- Application persistence only; not used for ML training.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    reports = relationship(
        "Report",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Report.created_at.desc()"
    )


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    narrative = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="reports")
    analyses = relationship(
        "Analysis",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="Analysis.created_at.desc()"
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)

    # Machine Learning Outputs
    ml_label = Column(String(20), nullable=False)
    ml_score = Column(Float, nullable=False)
    ml_threshold = Column(Float, nullable=False, default=0.59)
    decision_rationale = Column(Text, nullable=True)
    positive_evidence = Column(JSON, nullable=True)
    negative_evidence = Column(JSON, nullable=True)

    # V2.3 Deterministic Rule Engine Outputs
    rule_label = Column(String(20), nullable=False)
    rule_reason_code = Column(String(100), nullable=True)
    rule_energy = Column(String(100), nullable=True)
    rule_barrier = Column(String(100), nullable=True)
    rule_exposure = Column(String(100), nullable=True)
    rule_evidence_sufficiency = Column(String(50), nullable=True)
    precursor_type = Column(String(100), nullable=True)
    confidence = Column(String(50), nullable=True)

    # SIF Categorical Reconciliation Outputs
    reconciliation_status = Column(String(50), nullable=False, index=True)
    reconciliation_priority = Column(String(20), nullable=False, index=True)
    human_review_required = Column(Boolean, nullable=False, index=True)
    discrepancy = Column(Boolean, nullable=False)
    explanation = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    report = relationship("Report", back_populates="analyses")

