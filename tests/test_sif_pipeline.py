"""
Integration Tests for SIF End-to-End Pipeline
Phase 7.2 — SIH26165

Validates:
1. Full pipeline execution via analyze_report() on representative incidents.
2. String and dictionary narrative input formats.
3. Metadata quarantine rejection on pipeline input.
4. Schema compliance with Phase 7.2 Section 8 specifications.
5. Injected mock engines verifying all reconciliation branches through the pipeline.
6. Absolute separation of concerns between preprocessing, ML, rules, and reconciliation.
"""

import pytest
from sif_pipeline import analyze_report, normalize_narrative
from sif_reconciliation_engine import (
    STATUS_CONSENSUS_SIF,
    STATUS_CONSENSUS_NON_SIF,
    STATUS_RULE_UNCERTAIN_ML_SIGNAL,
    STATUS_RULE_UNCERTAIN_NO_ML_SIGNAL,
    STATUS_DIRECT_DISAGREEMENT,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW
)


# =============================================================================
# 1. End-to-End Real Engine Inference Tests
# =============================================================================

def test_pipeline_consensus_sif():
    """High-energy fall incident produces CONSENSUS_SIF with HIGH review priority."""
    narrative = "An employee was framing a roof and fell 28 feet to the ground when the scaffold collapsed."
    result = analyze_report(narrative)

    # Narrative block
    assert result["narrative"] == narrative

    # ML block
    assert result["ml"]["label"] == "YES"
    assert result["ml"]["score"] >= 0.59
    assert isinstance(result["ml"]["positive_evidence"], list)

    # Rule block
    assert result["rule"]["label"] == "YES"
    assert result["rule"]["energy"] == "GRAVITATIONAL"
    assert result["rule"]["reason_code"] == "GRAVITATIONAL_EXPOSURE"

    # Reconciliation block
    assert result["reconciliation"]["status"] == STATUS_CONSENSUS_SIF
    assert result["reconciliation"]["priority"] == PRIORITY_HIGH
    assert result["reconciliation"]["discrepancy"] is False
    assert result["reconciliation"]["review_required"] is False
    assert "Consensus SIF" in result["reconciliation"]["explanation"]


def test_pipeline_consensus_non_sif_medical():
    """Natural medical event produces CONSENSUS_NON_SIF with LOW review priority."""
    narrative = "An employee was seated in the conference room and suffered a fatal cardiac arrest."
    result = analyze_report(narrative)

    # ML block
    assert result["ml"]["label"] == "NO"
    assert result["ml"]["score"] < 0.59

    # Rule block
    assert result["rule"]["label"] == "NO"
    assert result["rule"]["reason_code"] == "NATURAL_MEDICAL_EVENT"

    # Reconciliation block
    assert result["reconciliation"]["status"] == STATUS_CONSENSUS_NON_SIF
    assert result["reconciliation"]["priority"] == PRIORITY_LOW
    assert result["reconciliation"]["discrepancy"] is False
    assert result["reconciliation"]["review_required"] is False
    assert "Consensus Non-SIF" in result["reconciliation"]["explanation"]


def test_pipeline_consensus_non_sif_low_energy():
    """Same-level fall with routine injury produces CONSENSUS_NON_SIF."""
    narrative = "An employee slipped and fell on ice on the sidewalk outside the entrance, bruising his knee."
    result = analyze_report(narrative)

    # ML block
    assert result["ml"]["label"] == "NO"
    assert result["ml"]["score"] < 0.59

    # Rule block
    assert result["rule"]["label"] == "NO"
    assert result["rule"]["reason_code"] == "LOW_ENERGY_SAME_LEVEL_FALL"

    # Reconciliation block
    assert result["reconciliation"]["status"] == STATUS_CONSENSUS_NON_SIF
    assert result["reconciliation"]["priority"] == PRIORITY_LOW
    assert result["reconciliation"]["discrepancy"] is False
    assert result["reconciliation"]["review_required"] is False


def test_pipeline_uncertain_narrative():
    """Brief, non-descriptive narrative triggers UNCERTAIN rule result and appropriate triage."""
    narrative = "Worker was injured on site during normal shift operations."
    result = analyze_report(narrative)

    assert result["rule"]["label"] == "UNCERTAIN"
    assert result["rule"]["reason_code"] == "INSUFFICIENT_INFORMATION"
    assert result["reconciliation"]["status"] in [
        STATUS_RULE_UNCERTAIN_ML_SIGNAL,
        STATUS_RULE_UNCERTAIN_NO_ML_SIGNAL
    ]
    assert result["reconciliation"]["discrepancy"] is True
    assert result["reconciliation"]["review_required"] is True


# =============================================================================
# 2. Input Formats & Normalization
# =============================================================================

def test_pipeline_dict_input():
    """Accepts dictionary with 'normalized_narrative' or 'narrative' key."""
    payload1 = {"normalized_narrative": "Worker fell 20 feet from extension ladder."}
    result1 = analyze_report(payload1)
    assert result1["reconciliation"]["status"] == STATUS_CONSENSUS_SIF

    payload2 = {"narrative": "Worker fell 20 feet from extension ladder."}
    result2 = analyze_report(payload2)
    assert result2["reconciliation"]["status"] == STATUS_CONSENSUS_SIF


def test_pipeline_normalization():
    """Normalizes excessive whitespace and carriage returns."""
    messy = "   Worker fell    15 feet \n\n from   scaffolding.   "
    clean = normalize_narrative(messy)
    assert clean == "Worker fell 15 feet from scaffolding."


def test_pipeline_invalid_inputs():
    """Rejects empty, non-string, or missing narrative payloads."""
    with pytest.raises(ValueError, match="Narrative must not be empty"):
        analyze_report("")

    with pytest.raises(ValueError, match="Narrative must not be empty"):
        analyze_report("    ")

    with pytest.raises(TypeError, match="Expected str or dict"):
        analyze_report(12345)

    with pytest.raises(ValueError, match="must contain 'normalized_narrative' or 'narrative'"):
        analyze_report({"wrong_key": "some text"})


# =============================================================================
# 3. Metadata Quarantine Enforcement in Pipeline
# =============================================================================

def test_pipeline_metadata_quarantine():
    """Rejects input dictionaries containing quarantined metadata keys."""
    bad_inputs = [
        {"narrative": "Worker fell 10 ft.", "hospitalized": 1},
        {"narrative": "Worker fell 10 ft.", "amputation": 1},
        {"narrative": "Worker fell 10 ft.", "fatal": 0},
        {"narrative": "Worker fell 10 ft.", "source_event_code": "123"},
        {"narrative": "Worker fell 10 ft.", "candidate_stratum": "TIER1"}
    ]
    for bad_dict in bad_inputs:
        with pytest.raises(ValueError, match="Metadata quarantine violation"):
            analyze_report(bad_dict)


# =============================================================================
# 4. Dependency Injection for Comprehensive State Coverage
# =============================================================================

class MockMLPredictor:
    def __init__(self, label: str, score: float):
        self.label = label
        self.score = score

    def predict(self, text: str):
        return {
            "ml_label": self.label,
            "ml_score": self.score,
            "threshold": 0.59,
            "positive_evidence": [{"feature": "mock_pos", "contribution": 0.5}],
            "negative_evidence": [],
            "decision_rationale": f"Mock ML rationale ({self.label}, score={self.score})"
        }


class MockRuleEngine:
    def __init__(self, label: str, energy: str = "UNKNOWN", reason: str = "UNKNOWN"):
        self.label = label
        self.energy = energy
        self.reason = reason

    def annotate_narrative(self, text: str):
        return {
            "sif_label": self.label,
            "sif_precursor_type": "MOCK_TYPE",
            "controlling_hazard_energy": self.energy,
            "barrier_state": "MOCK_BARRIER",
            "reason_code": self.reason
        }


def test_pipeline_direct_disagreement_ml_yes_rule_no():
    """Injected mock verifying DIRECT_DISAGREEMENT when ML=YES and Rule=NO."""
    mock_ml = MockMLPredictor("YES", 0.85)
    mock_rule = MockRuleEngine("NO", energy="UNKNOWN", reason="ROUTINE_NON_HAZARDOUS")

    result = analyze_report(
        narrative="Test narrative string for injection.",
        ml_predictor=mock_ml,
        rule_engine=mock_rule
    )

    assert result["reconciliation"]["status"] == STATUS_DIRECT_DISAGREEMENT
    assert result["reconciliation"]["priority"] == PRIORITY_HIGH
    assert result["reconciliation"]["discrepancy"] is True
    assert result["reconciliation"]["review_required"] is True
    assert "Direct Domain Disagreement" in result["reconciliation"]["explanation"]


def test_pipeline_direct_disagreement_ml_no_rule_yes():
    """Injected mock verifying DIRECT_DISAGREEMENT when ML=NO and Rule=YES."""
    mock_ml = MockMLPredictor("NO", 0.25)
    mock_rule = MockRuleEngine("YES", energy="PRESSURE_RELEASE", reason="PRESSURE_RELEASE")

    result = analyze_report(
        narrative="Test narrative string for injection.",
        ml_predictor=mock_ml,
        rule_engine=mock_rule
    )

    assert result["reconciliation"]["status"] == STATUS_DIRECT_DISAGREEMENT
    assert result["reconciliation"]["priority"] == PRIORITY_HIGH
    assert result["reconciliation"]["discrepancy"] is True
    assert result["reconciliation"]["review_required"] is True
    assert "Direct Domain Disagreement" in result["reconciliation"]["explanation"]


def test_pipeline_mock_rule_uncertain_ml_signal():
    """Injected mock verifying RULE_UNCERTAIN_ML_SIGNAL."""
    mock_ml = MockMLPredictor("YES", 0.77)
    mock_rule = MockRuleEngine("UNCERTAIN", energy="UNKNOWN", reason="INSUFFICIENT_INFORMATION")

    result = analyze_report(
        narrative="Test narrative string for injection.",
        ml_predictor=mock_ml,
        rule_engine=mock_rule
    )

    assert result["reconciliation"]["status"] == STATUS_RULE_UNCERTAIN_ML_SIGNAL
    assert result["reconciliation"]["priority"] == PRIORITY_HIGH
    assert result["reconciliation"]["discrepancy"] is True
    assert result["reconciliation"]["review_required"] is True


def test_pipeline_mock_rule_uncertain_no_ml_signal():
    """Injected mock verifying RULE_UNCERTAIN_NO_ML_SIGNAL."""
    mock_ml = MockMLPredictor("NO", 0.12)
    mock_rule = MockRuleEngine("UNCERTAIN", energy="UNKNOWN", reason="INSUFFICIENT_INFORMATION")

    result = analyze_report(
        narrative="Test narrative string for injection.",
        ml_predictor=mock_ml,
        rule_engine=mock_rule
    )

    assert result["reconciliation"]["status"] == STATUS_RULE_UNCERTAIN_NO_ML_SIGNAL
    assert result["reconciliation"]["priority"] == PRIORITY_MEDIUM
    assert result["reconciliation"]["discrepancy"] is True
    assert result["reconciliation"]["review_required"] is True
