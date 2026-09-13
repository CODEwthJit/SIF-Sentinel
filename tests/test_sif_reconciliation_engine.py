"""
Unit Tests for SIF Reconciliation Engine
Phase 7.2 — SIH26165

Validates:
1. All 6 categorical ML / Rule combinations:
   - ML YES + Rule YES -> CONSENSUS_SIF (HIGH)
   - ML NO + Rule NO -> CONSENSUS_NON_SIF (LOW)
   - ML YES + Rule UNCERTAIN -> RULE_UNCERTAIN_ML_SIGNAL (HIGH)
   - ML NO + Rule UNCERTAIN -> RULE_UNCERTAIN_NO_ML_SIGNAL (MEDIUM)
   - ML YES + Rule NO -> DIRECT_DISAGREEMENT (HIGH)
   - ML NO + Rule YES -> DIRECT_DISAGREEMENT (HIGH)
2. Strict input validation and rejection of malformed payloads
3. Rejection of scores outside [0.0, 1.0]
4. Metadata quarantine enforcement (prohibiting outcome and administrative fields)
5. Zero numerical weighted formulas (strictly categorical triage)
6. Deterministic output behavior
7. Evidence-grounded explanations
8. Engine freeze immutability
"""

import pytest
from sif_reconciliation_engine import (
    SIFReconciliationEngine,
    reconcile_sif_evidence,
    STATUS_CONSENSUS_SIF,
    STATUS_CONSENSUS_NON_SIF,
    STATUS_RULE_UNCERTAIN_ML_SIGNAL,
    STATUS_RULE_UNCERTAIN_NO_ML_SIGNAL,
    STATUS_DIRECT_DISAGREEMENT,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
    PROHIBITED_METADATA_KEYS
)
from sif_auto_annotator_v23 import SIFAutoAnnotatorV23
from ml.sif_ml_predictor import SIFMLPredictor


@pytest.fixture
def reconciler():
    return SIFReconciliationEngine()


# =============================================================================
# 1. Six Categorical Matrix Combinations
# =============================================================================

def test_consensus_sif(reconciler):
    """ML YES + Rule YES -> CONSENSUS_SIF (Priority: HIGH, Discrepancy: False, Review: False)"""
    payload = {
        "narrative": "Worker fell 25 feet from scaffold when plank snapped.",
        "ml_result": {
            "ml_label": "YES",
            "ml_score": 0.9650,
            "threshold": 0.59
        },
        "rule_result": {
            "sif_label": "YES",
            "sif_precursor_type": "HIGH_ENERGY_FATAL_COLLAPSE",
            "controlling_hazard_energy": "GRAVITATIONAL",
            "barrier_state": "DAMAGED_OR_MISSING",
            "reason_code": "GRAVITATIONAL_EXPOSURE"
        }
    }
    result = reconciler.reconcile(payload=payload)

    assert result["reconciliation_status"] == STATUS_CONSENSUS_SIF
    assert result["review_priority"] == PRIORITY_HIGH
    assert result["discrepancy_flag"] is False
    assert result["review_required"] is False
    assert "Consensus SIF" in result["explanation"]
    assert "0.9650" in result["explanation"]
    assert "GRAVITATIONAL" in result["explanation"]


def test_consensus_non_sif(reconciler):
    """ML NO + Rule NO -> CONSENSUS_NON_SIF (Priority: LOW, Discrepancy: False, Review: False)"""
    payload = {
        "narrative": "Worker suffered a natural heart attack while sitting at desk in office.",
        "ml_result": {
            "ml_label": "NO",
            "ml_score": 0.0820,
            "threshold": 0.59
        },
        "rule_result": {
            "sif_label": "NO",
            "sif_precursor_type": "NO_SIF_POTENTIAL",
            "controlling_hazard_energy": "UNKNOWN",
            "barrier_state": "NOT_APPLICABLE",
            "reason_code": "NATURAL_MEDICAL_EVENT"
        }
    }
    result = reconciler.reconcile(payload=payload)

    assert result["reconciliation_status"] == STATUS_CONSENSUS_NON_SIF
    assert result["review_priority"] == PRIORITY_LOW
    assert result["discrepancy_flag"] is False
    assert result["review_required"] is False
    assert "Consensus Non-SIF" in result["explanation"]
    assert "0.0820" in result["explanation"]
    assert "NATURAL_MEDICAL_EVENT" in result["explanation"]


def test_rule_uncertain_ml_signal(reconciler):
    """ML YES + Rule UNCERTAIN -> RULE_UNCERTAIN_ML_SIGNAL (Priority: HIGH, Discrepancy: True, Review: True)"""
    payload = {
        "narrative": "Worker observed equipment failure near high pressure pneumatic valve.",
        "ml_result": {
            "ml_label": "YES",
            "ml_score": 0.8450,
            "threshold": 0.59
        },
        "rule_result": {
            "sif_label": "UNCERTAIN",
            "sif_precursor_type": "UNCERTAIN",
            "controlling_hazard_energy": "PRESSURE",
            "barrier_state": "UNKNOWN",
            "reason_code": "INSUFFICIENT_INFORMATION"
        }
    }
    result = reconciler.reconcile(payload=payload)

    assert result["reconciliation_status"] == STATUS_RULE_UNCERTAIN_ML_SIGNAL
    assert result["review_priority"] == PRIORITY_HIGH
    assert result["discrepancy_flag"] is True
    assert result["review_required"] is True
    assert "ML Signal" in result["explanation"]
    assert "0.8450" in result["explanation"]


def test_rule_uncertain_no_ml_signal(reconciler):
    """ML NO + Rule UNCERTAIN -> RULE_UNCERTAIN_NO_ML_SIGNAL (Priority: MEDIUM, Discrepancy: True, Review: True)"""
    payload = {
        "narrative": "Employee reported feeling dizzy during afternoon shift with no hazard described.",
        "ml_result": {
            "ml_label": "NO",
            "ml_score": 0.2100,
            "threshold": 0.59
        },
        "rule_result": {
            "sif_label": "UNCERTAIN",
            "sif_precursor_type": "UNCERTAIN",
            "controlling_hazard_energy": "UNKNOWN",
            "barrier_state": "UNKNOWN",
            "reason_code": "INSUFFICIENT_INFORMATION"
        }
    }
    result = reconciler.reconcile(payload=payload)

    assert result["reconciliation_status"] == STATUS_RULE_UNCERTAIN_NO_ML_SIGNAL
    assert result["review_priority"] == PRIORITY_MEDIUM
    assert result["discrepancy_flag"] is True
    assert result["review_required"] is True
    assert "No ML Signal" in result["explanation"]
    assert "0.2100" in result["explanation"]


def test_direct_disagreement_ml_yes_rule_no(reconciler):
    """ML YES + Rule NO -> DIRECT_DISAGREEMENT (Priority: HIGH, Discrepancy: True, Review: True)"""
    payload = {
        "narrative": "Worker tripped on level concrete walkway and grazed knee.",
        "ml_result": {
            "ml_label": "YES",
            "ml_score": 0.7350,
            "threshold": 0.59
        },
        "rule_result": {
            "sif_label": "NO",
            "sif_precursor_type": "NO_SIF_POTENTIAL",
            "controlling_hazard_energy": "GRAVITATIONAL",
            "barrier_state": "NOT_APPLICABLE",
            "reason_code": "LOW_ENERGY_SAME_LEVEL_FALL"
        }
    }
    result = reconciler.reconcile(payload=payload)

    assert result["reconciliation_status"] == STATUS_DIRECT_DISAGREEMENT
    assert result["review_priority"] == PRIORITY_HIGH
    assert result["discrepancy_flag"] is True
    assert result["review_required"] is True
    assert "Direct Domain Disagreement" in result["explanation"]
    assert "0.7350" in result["explanation"]
    assert "LOW_ENERGY_SAME_LEVEL_FALL" in result["explanation"]


def test_direct_disagreement_ml_no_rule_yes(reconciler):
    """ML NO + Rule YES -> DIRECT_DISAGREEMENT (Priority: HIGH, Discrepancy: True, Review: True)"""
    payload = {
        "narrative": "Specialized valve rupture released pressurized ammonia gas cloud into mechanical room.",
        "ml_result": {
            "ml_label": "NO",
            "ml_score": 0.3800,
            "threshold": 0.59
        },
        "rule_result": {
            "sif_label": "YES",
            "sif_precursor_type": "HIGH_ENERGY_RELEASE",
            "controlling_hazard_energy": "PRESSURE_RELEASE",
            "barrier_state": "FAILED_OR_BREACHED",
            "reason_code": "PRESSURE_RELEASE"
        }
    }
    result = reconciler.reconcile(payload=payload)

    assert result["reconciliation_status"] == STATUS_DIRECT_DISAGREEMENT
    assert result["review_priority"] == PRIORITY_HIGH
    assert result["discrepancy_flag"] is True
    assert result["review_required"] is True
    assert "Direct Domain Disagreement" in result["explanation"]
    assert "0.3800" in result["explanation"]
    assert "PRESSURE_RELEASE" in result["explanation"]


# =============================================================================
# 2. Strict Input Validation & Schema Enforcement
# =============================================================================

def test_malformed_ml_result_rejected(reconciler):
    """Verify rejection when ml_result is missing, non-dict, or has invalid labels."""
    base_payload = {
        "narrative": "Worker injured.",
        "rule_result": {"sif_label": "YES"}
    }

    # Missing ml_result
    with pytest.raises(ValueError, match="Missing required key.*ml_result"):
        reconciler.reconcile(payload=base_payload)

    # Non-dict ml_result
    with pytest.raises(TypeError, match="Field 'ml_result' must be a dict"):
        reconciler.reconcile(payload={**base_payload, "ml_result": "invalid"})

    # Invalid ml_label
    with pytest.raises(ValueError, match="Invalid or missing 'ml_label'"):
        reconciler.reconcile(payload={**base_payload, "ml_result": {"ml_label": "MAYBE", "ml_score": 0.5}})

    # Missing ml_score
    with pytest.raises(ValueError, match="Missing 'ml_score'"):
        reconciler.reconcile(payload={**base_payload, "ml_result": {"ml_label": "YES"}})

    # Non-numeric ml_score
    with pytest.raises(ValueError, match="must be a numeric float"):
        reconciler.reconcile(payload={**base_payload, "ml_result": {"ml_label": "YES", "ml_score": "not_a_number"}})


def test_malformed_rule_result_rejected(reconciler):
    """Verify rejection when rule_result is missing, non-dict, or has invalid labels."""
    base_payload = {
        "narrative": "Worker injured.",
        "ml_result": {"ml_label": "YES", "ml_score": 0.8}
    }

    # Missing rule_result
    with pytest.raises(ValueError, match="Missing required key.*rule_result"):
        reconciler.reconcile(payload=base_payload)

    # Non-dict rule_result
    with pytest.raises(TypeError, match="Field 'rule_result' must be a dict"):
        reconciler.reconcile(payload={**base_payload, "rule_result": 42})

    # Invalid sif_label
    with pytest.raises(ValueError, match="Invalid or missing 'sif_label'"):
        reconciler.reconcile(payload={**base_payload, "rule_result": {"sif_label": "POSSIBLE"}})


def test_score_outside_0_1_rejected(reconciler):
    """Verify rejection of ML scores outside [0.0, 1.0]."""
    base_payload = {
        "narrative": "Worker fell from ladder.",
        "rule_result": {"sif_label": "YES"}
    }

    with pytest.raises(ValueError, match="bounded in \\[0.0, 1.0\\]"):
        reconciler.reconcile(payload={**base_payload, "ml_result": {"ml_label": "YES", "ml_score": -0.05}})

    with pytest.raises(ValueError, match="bounded in \\[0.0, 1.0\\]"):
        reconciler.reconcile(payload={**base_payload, "ml_result": {"ml_label": "YES", "ml_score": 1.01}})

    with pytest.raises(ValueError, match="bounded in \\[0.0, 1.0\\]"):
        reconciler.reconcile(payload={**base_payload, "ml_result": {"ml_label": "YES", "ml_score": 95.0}})


def test_empty_narrative_rejected(reconciler):
    """Verify rejection of empty or whitespace-only narratives."""
    payload = {
        "ml_result": {"ml_label": "YES", "ml_score": 0.8},
        "rule_result": {"sif_label": "YES"}
    }

    with pytest.raises(ValueError, match="Missing required key.*narrative"):
        reconciler.reconcile(payload=payload)

    with pytest.raises(ValueError, match="must be a non-empty string"):
        reconciler.reconcile(payload={**payload, "narrative": "   "})


# =============================================================================
# 3. Metadata Quarantine Enforcement
# =============================================================================

def test_metadata_quarantine_enforced(reconciler):
    """Verify that any quarantined metadata keys are strictly rejected."""
    valid_base = {
        "narrative": "Worker fell 15 feet from roof.",
        "ml_result": {"ml_label": "YES", "ml_score": 0.95},
        "rule_result": {"sif_label": "YES"}
    }

    # Prohibited keys at top level
    for bad_key in ["hospitalized", "amputation", "fatal", "source_event_code", "reference_outcome_context"]:
        with pytest.raises(ValueError, match="Metadata quarantine violation"):
            reconciler.reconcile(payload={**valid_base, bad_key: 1})

    # Prohibited keys inside ml_result
    bad_ml = {"ml_label": "YES", "ml_score": 0.9, "hospitalized": 1}
    with pytest.raises(ValueError, match="Metadata quarantine violation.*ml_result"):
        reconciler.reconcile(payload={**valid_base, "ml_result": bad_ml})

    # Prohibited keys inside rule_result
    bad_rule = {"sif_label": "YES", "fatal": 1}
    with pytest.raises(ValueError, match="Metadata quarantine violation.*rule_result"):
        reconciler.reconcile(payload={**valid_base, "rule_result": bad_rule})


# =============================================================================
# 4. Zero Numerical Weighted Formula & Determinism
# =============================================================================

def test_no_numerical_weighted_formula(reconciler):
    """
    Asserts that NO continuous weighted formula or blended score exists.
    Status and priority are strictly categorical and discrete.
    """
    # High score vs moderate score with same YES/YES label
    res_high = reconciler.reconcile(
        narrative="Test fall narrative.",
        ml_result={"ml_label": "YES", "ml_score": 0.99},
        rule_result={"sif_label": "YES", "controlling_hazard_energy": "GRAVITATIONAL"}
    )
    res_mod = reconciler.reconcile(
        narrative="Test fall narrative.",
        ml_result={"ml_label": "YES", "ml_score": 0.60},
        rule_result={"sif_label": "YES", "controlling_hazard_energy": "GRAVITATIONAL"}
    )

    # Both must have identical categorical outputs
    assert res_high["reconciliation_status"] == res_mod["reconciliation_status"] == STATUS_CONSENSUS_SIF
    assert res_high["review_priority"] == res_mod["review_priority"] == PRIORITY_HIGH
    assert res_high["discrepancy_flag"] == res_mod["discrepancy_flag"] is False

    # Prohibit any continuous synthetic score fields in output
    for prohibited_score_field in ["final_score", "combined_score", "weighted_score", "risk_score", "sif_probability"]:
        assert prohibited_score_field not in res_high
        assert prohibited_score_field not in res_mod


def test_deterministic_output(reconciler):
    """Asserts that identical inputs produce identical outputs deterministically."""
    payload = {
        "narrative": "Worker operating milling machine got glove caught in spindle.",
        "ml_result": {"ml_label": "YES", "ml_score": 0.9123},
        "rule_result": {"sif_label": "YES", "reason_code": "MECHANICAL_ENTANGLEMENT", "controlling_hazard_energy": "MECHANICAL"}
    }

    first = reconciler.reconcile(payload=payload)
    for _ in range(25):
        repeat = reconciler.reconcile(payload=payload)
        assert first == repeat


def test_convenience_wrapper():
    """Verify module-level convenience function reconcile_sif_evidence()."""
    res = reconcile_sif_evidence(
        narrative="Worker slipped on ice and bruised elbow.",
        ml_result={"ml_label": "NO", "ml_score": 0.15},
        rule_result={"sif_label": "NO", "reason_code": "LOW_ENERGY_SAME_LEVEL_FALL"}
    )
    assert res["reconciliation_status"] == STATUS_CONSENSUS_NON_SIF
    assert res["review_priority"] == PRIORITY_LOW


# =============================================================================
# 5. Engine Immutability & Safety Boundary
# =============================================================================

def test_frozen_engines_immutability():
    """Verify underlying ML predictor and V2.3 rule engine remain frozen and untouched."""
    rule_engine = SIFAutoAnnotatorV23()
    assert rule_engine.version == "2.3.0-SPEC-DESIGN"

    ml_predictor = SIFMLPredictor()
    assert ml_predictor.threshold == 0.59
    assert ml_predictor.intercept is not None
    assert len(ml_predictor.coefficients) > 0

