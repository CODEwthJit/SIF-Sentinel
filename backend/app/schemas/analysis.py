"""
Pydantic Schemas for SIF Analysis & Explainability
Phase 9.1 — SIH26165
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.reports import ReportOut


class LexicalEvidenceItem(BaseModel):
    feature: str = Field(..., description="Lexical token or n-gram present in the incident narrative.")
    contribution: float = Field(..., description="Contribution score (x_j * w_j) pushing or pulling SIF propensity.")
    tfidf_value: Optional[float] = Field(None, description="TF-IDF term frequency value.")
    weight: Optional[float] = Field(None, description="Logistic regression feature coefficient.")


class MLEvidenceSchema(BaseModel):
    label: str = Field(..., description="Statistical class prediction: 'YES' or 'NO'.")
    score: float = Field(
        ...,
        description="Model-estimated propensity for the provisional SIF precursor YES class under V2.3 labels. Not a probability of death or injury."
    )
    threshold: float = Field(0.59, description="Locked operational decision threshold.")
    positive_evidence: List[LexicalEvidenceItem] = Field(
        default_factory=list,
        description="Top lexical n-grams increasing SIF propensity."
    )
    negative_evidence: List[LexicalEvidenceItem] = Field(
        default_factory=list,
        description="Top lexical n-grams mitigating SIF propensity."
    )
    decision_rationale: Optional[str] = Field(
        None,
        description="Textual explanation of statistical feature attributions."
    )


class RuleEvidenceSchema(BaseModel):
    label: str = Field(..., description="Deterministic SIF label: 'YES', 'NO', or 'UNCERTAIN'.")
    reason_code: Optional[str] = Field(None, description="Controlled reason taxonomy code.")
    controlling_hazard_energy: Optional[str] = Field(None, description="Identified high-hazard physical energy type.")
    barrier_state: Optional[str] = Field(None, description="Status of physical or administrative barrier.")
    human_exposure: Optional[str] = Field(None, description="Direct or indirect worker exposure mode.")
    evidence_sufficiency: Optional[str] = Field(None, description="Assessment of text factual completeness.")
    precursor_type: Optional[str] = Field(None, description="Specific precursor mechanism taxonomy.")
    confidence: Optional[str] = Field(None, description="Rule deduction confidence tier.")


class ReconciliationSchema(BaseModel):
    status: str = Field(
        ...,
        description="Categorical agreement state: CONSENSUS_SIF, CONSENSUS_NON_SIF, RULE_UNCERTAIN_ML_SIGNAL, RULE_UNCERTAIN_NO_ML_SIGNAL, or DIRECT_DISAGREEMENT."
    )
    priority: str = Field(..., description="Operational review triage priority: 'HIGH', 'MEDIUM', or 'LOW'.")
    discrepancy: bool = Field(..., description="True if ML and Rule outputs diverge or if ambiguity exists.")
    review_required: bool = Field(..., description="True if gated for mandatory human safety professional audit.")
    explanation: Optional[str] = Field(None, description="Deterministic evidence-grounded audit rationale.")


class AnalysisResponse(BaseModel):
    report: ReportOut = Field(..., description="Persisted incident report entity.")
    ml: MLEvidenceSchema = Field(..., description="Machine learning statistical evidence block.")
    rule: RuleEvidenceSchema = Field(..., description="Deterministic V2.3 rule engine reasoning block.")
    reconciliation: ReconciliationSchema = Field(..., description="Categorical reconciliation and triage assessment.")


class ReportDetailResponse(BaseModel):
    report: ReportOut
    latest_analysis: Optional[AnalysisResponse] = None
    total_analyses: int = 0

