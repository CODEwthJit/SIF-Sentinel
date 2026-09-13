"""
tests/test_sif_engine_v23.py
============================
Executable Pytest Suite for SIF Label Engine V2.3
Specification Reference: SIF_LABEL_ENGINE_V2.3_SPEC.md
Behavioral Contract: tests/test_sif_engine_v23_spec_contract.md

Executes:
1. All 52 behavioral test cases across the 8 mandatory safety reasoning families.
2. Runtime metadata quarantine integrity tests.
3. Controlled vocabulary adherence tests.
4. Verbatim evidence substring extraction verification.
"""

import os
import re
import pytest
from sif_auto_annotator_v23 import (
    SIFAutoAnnotatorV23,
    ALLOWED_SIF_LABELS,
    ALLOWED_SIF_PRECURSOR_TYPES,
    ALLOWED_HAZARD_ENERGIES,
    ALLOWED_HUMAN_EXPOSURES,
    ALLOWED_BARRIER_STATES,
    ALLOWED_EVIDENCE_SUFFICIENCY,
    ALLOWED_CAUSAL_NATURES,
    ALLOWED_REASON_CODES,
    ALLOWED_CONFIDENCE,
    PROHIBITED_METADATA_COLUMNS
)

def load_contract_cases():
    contract_path = os.path.join(os.path.dirname(__file__), "test_sif_engine_v23_spec_contract.md")
    with open(contract_path, "r", encoding="utf-8") as f:
        text = f.read()

    cases = []
    for line in text.split("\n"):
        if line.startswith("| **TC-"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            tc_id = parts[0].replace("*", "").strip()
            narrative = parts[1].replace("*", "").strip()
            # Clean trailing pilot reference if present
            if " (PILOT_" in narrative:
                narrative = narrative[:narrative.rfind(" (PILOT_")].strip()
            elif " (`PILOT_" in narrative:
                narrative = narrative[:narrative.rfind(" (`PILOT_")].strip()

            energy = parts[2].replace("`", "").strip()
            exposure = parts[3].replace("`", "").strip()
            barrier = parts[4].replace("`", "").strip()
            consequence = parts[5].replace("`", "").strip()
            label = parts[6].replace("`", "").replace("*", "").strip()
            reason = parts[7].replace("`", "").strip()
            cases.append((tc_id, narrative, energy, exposure, barrier, consequence, label, reason))
    return cases

CONTRACT_CASES = load_contract_cases()

@pytest.fixture(scope="module")
def annotator():
    return SIFAutoAnnotatorV23()

# =============================================================================
# 1. BEHAVIORAL CONTRACT TESTS (52 CASES)
# =============================================================================
@pytest.mark.parametrize("tc_id,narrative,expected_energy,expected_exposure,expected_barrier,expected_consequence,expected_label,expected_reason", CONTRACT_CASES)
def test_v23_behavioral_contract(annotator, tc_id, narrative, expected_energy, expected_exposure, expected_barrier, expected_consequence, expected_label, expected_reason):
    res = annotator.annotate_narrative(narrative)

    assert res["sif_label"] == expected_label, f"[{tc_id}] Expected label {expected_label}, got {res['sif_label']}"
    assert res["reason_code"] == expected_reason, f"[{tc_id}] Expected reason {expected_reason}, got {res['reason_code']}"
    
    # Check energy category if expected
    if expected_energy != "UNKNOWN":
        assert res["controlling_hazard_energy"] == expected_energy, f"[{tc_id}] Expected energy {expected_energy}, got {res['controlling_hazard_energy']}"

    # Verbatim Evidence Check for YES and NO
    if res["sif_label"] in ["YES", "NO"]:
        ev = res["evidence_text"]
        assert ev, f"[{tc_id}] Evidence text must not be empty for {res['sif_label']}"
        assert ev in narrative, f"[{tc_id}] Evidence text '{ev}' must be a verbatim substring of narrative"

# =============================================================================
# 2. RUNTIME METADATA QUARANTINE INTEGRITY TESTS
# =============================================================================
def test_metadata_quarantine_integrity(annotator):
    """
    Verifies that contaminated metadata columns (severe outcomes, event codes, etc.)
    have ZERO effect on classification decisions.
    """
    clean_record = {
        "normalized_narrative": "An employee slipped and fell on ice on the sidewalk outside the entrance, bruising his knee."
    }
    
    contaminated_record = clean_record.copy()
    contaminated_record["hospitalized"] = "1"
    contaminated_record["amputation"] = "1"
    contaminated_record["source_event_title"] = "Fall from roof to lower level"
    contaminated_record["hazard_stratum"] = "High Voltage Explosion"
    contaminated_record["sif_label"] = "YES"

    clean_res = annotator.annotate_record(clean_record)
    contam_res = annotator.annotate_record(contaminated_record)

    # Classification must be identical regardless of metadata contamination
    assert clean_res["sif_label"] == "NO"
    assert contam_res["sif_label"] == "NO"
    assert clean_res["reason_code"] == "LOW_ENERGY_SAME_LEVEL_FALL"
    assert contam_res["reason_code"] == "LOW_ENERGY_SAME_LEVEL_FALL"

# =============================================================================
# 3. CONTROLLED VOCABULARY ADHERENCE TESTS
# =============================================================================
def test_vocabulary_adherence(annotator):
    """Verifies that all output fields match approved ontology enums."""
    sample_narrative = "An employee fell 15 feet from a scaffold when planking broke."
    res = annotator.annotate_narrative(sample_narrative)

    assert res["sif_label"] in ALLOWED_SIF_LABELS
    assert res["sif_precursor_type"] in ALLOWED_SIF_PRECURSOR_TYPES
    assert res["controlling_hazard_energy"] in ALLOWED_HAZARD_ENERGIES
    assert res["human_exposure"] in ALLOWED_HUMAN_EXPOSURES
    assert res["barrier_state"] in ALLOWED_BARRIER_STATES
    assert res["evidence_sufficiency"] in ALLOWED_EVIDENCE_SUFFICIENCY
    assert res["causal_nature"] in ALLOWED_CAUSAL_NATURES
    assert res["reason_code"] in ALLOWED_REASON_CODES
    assert res["confidence"] in ALLOWED_CONFIDENCE

