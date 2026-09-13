"""
SIF End-to-End Pipeline
Phase 7.2 — SIH26165

Integrated analysis pipeline combining:
1. NLP preprocessing and normalization
2. Machine Learning inference (Phase 6.1 TF-IDF Baseline, frozen)
3. Deterministic Domain Rule Engine (V2.3 Frozen Engine)
4. SIF Reconciliation Engine (Categorical Triage Matrix)

Architecture:
    Raw Narrative
          ↓
    NLP Preprocessing
          ↓
     ┌────┴────┐
     ▼         ▼
    ML        V2.3
     │          │
     └────┬─────┘
          ▼
    Reconciliation
          ↓
    Final Auditable Result
"""

import os
import re
import sys
from typing import Dict, Any, Union, Optional

# Ensure project root and src are available for imports
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_CURRENT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

try:
    from sif_auto_annotator_v23 import SIFAutoAnnotatorV23
    from sif_reconciliation_engine import SIFReconciliationEngine, PROHIBITED_METADATA_KEYS
except ImportError:
    from src.sif_auto_annotator_v23 import SIFAutoAnnotatorV23
    from src.sif_reconciliation_engine import SIFReconciliationEngine, PROHIBITED_METADATA_KEYS

from ml.sif_ml_predictor import SIFMLPredictor


# Lazy singletons for efficiency
_ml_predictor: Optional[SIFMLPredictor] = None
_rule_engine: Optional[SIFAutoAnnotatorV23] = None
_reconciliation_engine: Optional[SIFReconciliationEngine] = None


def get_ml_predictor() -> SIFMLPredictor:
    global _ml_predictor
    if _ml_predictor is None:
        _ml_predictor = SIFMLPredictor()
    return _ml_predictor


def get_rule_engine() -> SIFAutoAnnotatorV23:
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = SIFAutoAnnotatorV23()
    return _rule_engine


def get_reconciliation_engine() -> SIFReconciliationEngine:
    global _reconciliation_engine
    if _reconciliation_engine is None:
        _reconciliation_engine = SIFReconciliationEngine()
    return _reconciliation_engine


def normalize_narrative(text: str) -> str:
    """
    Standardizes narrative text by stripping leading/trailing whitespace
    and collapsing multiple whitespace characters into single spaces.
    """
    if not isinstance(text, str):
        raise TypeError(f"Narrative must be a string, got {type(text).__name__}")
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        raise ValueError("Narrative must not be empty or whitespace-only.")
    return cleaned


def analyze_report(
    narrative: Union[str, Dict[str, Any]],
    ml_predictor: Optional[SIFMLPredictor] = None,
    rule_engine: Optional[SIFAutoAnnotatorV23] = None,
    reconciliation_engine: Optional[SIFReconciliationEngine] = None
) -> Dict[str, Any]:
    """
    End-to-end report analysis executing NLP preprocessing, ML prediction,
    V2.3 rule evaluation, and categorical reconciliation.

    Args:
        narrative: Incident narrative string or dictionary containing 'normalized_narrative'.
        ml_predictor: Optional injected SIFMLPredictor instance.
        rule_engine: Optional injected SIFAutoAnnotatorV23 instance.
        reconciliation_engine: Optional injected SIFReconciliationEngine instance.

    Returns:
        Structured dictionary containing:
            - narrative: Normalized incident text
            - ml: Machine learning prediction and lexical evidence
            - rule: Deterministic V2.3 engine classification and energy reasoning
            - reconciliation: Categorical status, review priority, discrepancy flag, and explanation
    """
    # 1. Metadata Quarantine & Input Normalization
    if isinstance(narrative, dict):
        # Strict feature quarantine: Disallow any outcome, administrative, or ontology fields
        prohibited = set(narrative.keys()).intersection(PROHIBITED_METADATA_KEYS)
        if prohibited:
            raise ValueError(
                f"Metadata quarantine violation: Prohibited keys detected in pipeline input: {sorted(list(prohibited))}."
            )
        raw_text = (
            narrative.get("normalized_narrative")
            or narrative.get("narrative")
            or narrative.get("original_narrative")
        )
        if raw_text is None:
            raise ValueError("Input dictionary must contain 'normalized_narrative' or 'narrative'.")
    elif isinstance(narrative, str):
        raw_text = narrative
    else:
        raise TypeError(f"Expected str or dict for narrative, got {type(narrative).__name__}")

    norm_narrative = normalize_narrative(raw_text)

    # 2. Acquire Engines
    ml = ml_predictor or get_ml_predictor()
    rule = rule_engine or get_rule_engine()
    reconciler = reconciliation_engine or get_reconciliation_engine()

    # 3. Independent Engine Evaluations (Zero Coupling)
    ml_output = ml.predict(norm_narrative)
    rule_output = rule.annotate_narrative(norm_narrative)

    # 4. Reconciliation
    reconciled = reconciler.reconcile(
        narrative=norm_narrative,
        ml_result=ml_output,
        rule_result=rule_output
    )

    # 5. Format Structured Contract (Adhering to Phase 7.2 Section 8)
    return {
        "narrative": norm_narrative,
        "ml": {
            "label": ml_output["ml_label"],
            "ml_label": ml_output["ml_label"],
            "score": ml_output["ml_score"],
            "ml_score": ml_output["ml_score"],
            "threshold": ml_output.get("threshold", 0.59),
            "positive_evidence": ml_output.get("positive_evidence", []),
            "negative_evidence": ml_output.get("negative_evidence", []),
            "decision_rationale": ml_output.get("decision_rationale", "")
        },
        "rule": {
            "label": rule_output["sif_label"],
            "sif_label": rule_output["sif_label"],
            "reason_code": rule_output.get("reason_code", "UNKNOWN"),
            "energy": rule_output.get("controlling_hazard_energy", "UNKNOWN"),
            "controlling_hazard_energy": rule_output.get("controlling_hazard_energy", "UNKNOWN"),
            "barrier": rule_output.get("barrier_state", "UNKNOWN"),
            "barrier_state": rule_output.get("barrier_state", "UNKNOWN"),
            "precursor_type": rule_output.get("sif_precursor_type", "UNKNOWN"),
            "sif_precursor_type": rule_output.get("sif_precursor_type", "UNKNOWN"),
            "human_exposure": rule_output.get("human_exposure", "UNKNOWN"),
            "evidence_sufficiency": rule_output.get("evidence_sufficiency", "UNKNOWN"),
            "confidence": rule_output.get("confidence", "UNKNOWN")
        },
        "reconciliation": {
            "status": reconciled["reconciliation_status"],
            "reconciliation_status": reconciled["reconciliation_status"],
            "priority": reconciled["review_priority"],
            "review_priority": reconciled["review_priority"],
            "discrepancy": reconciled["discrepancy_flag"],
            "discrepancy_flag": reconciled["discrepancy_flag"],
            "review_required": reconciled["review_required"],
            "explanation": reconciled["explanation"]
        }
    }

