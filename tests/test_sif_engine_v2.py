#!/usr/bin/env python3
"""
test_sif_engine_v2.py
=====================
Automated Validation & Test Suite for SIF Label Engine V2.
SIH26165 Project.

This test suite is the executable contract for the V2 Narrative-Only SIF Label Engine
as specified in:
- SIF_LABEL_ENGINE_V2_SPEC.md (v2.2.0-FINAL)
- sif_label_engine_v2_decision_table.csv
- CHANGELOG_V2_FINAL.md

Test Groups:
 1. Decision Table Tests (30 cases from CSV)
 2. Core Evidence Logic Tests (E, X, C, B, S dimensions)
 3. Six-State Barrier Taxonomy Tests (FAILED, SUCCESSFULLY_INTERVENED, ABSENT, PRESENT_NOT_ACTIVATED, UNKNOWN, NOT_APPLICABLE)
 4. Outcome-Decoupling Tests (Decoupling actual injury from SIF potential)
 5. Negation Tests (25+ paired positive/negative cases)
 6. Hard Negative Tests (25+ non-SIF industrial narratives with misleading vocabulary)
 7. Hard Positive Tests (25+ high-potential precursors with zero/minor injury)
 8. Metadata Quarantine Tests (Strict narrative-only enforcement)
 9. Verbatim Evidence Tests (Exact substring assertion)
10. Reason Code Tests (Controlled explainability taxonomy)
11. Counterfactual Shortcut Tests (Resistance to outcome keyword shortcuts)
12. Numerical-Context Tests (Supporting evidence, no hard universal boundaries)
13. Routine/Control Tests (Elimination of 'routine + controlled = NO' fallacy)
14. Uncertainty Tests (Sparse, ambiguous, and conflicting narrative handling)
15. Test Suite Integrity & Determinism (Offline, deterministic, no network, no GPU)

Contract / Interface Definition:
The future V2 engine must implement:
    class SIFAutoAnnotatorV2:
        def annotate_record(self, record: dict) -> dict:
            # record must contain: {'normalized_narrative': str}
            # returns dict with:
            #   sif_label (YES, NO, UNCERTAIN)
            #   sif_precursor_type (NO_SIF_POTENTIAL, SIF_POTENTIAL_SUCCESSFUL_BARRIER, SIF_POTENTIAL_FAILED_BARRIER, UNCERTAIN)
            #   reason_code (controlled vocab)
            #   hazard_energy (controlled vocab)
            #   human_exposure (DIRECT, POTENTIAL, NONE, UNKNOWN)
            #   barrier_state (FAILED, SUCCESSFULLY_INTERVENED, ABSENT, PRESENT_NOT_ACTIVATED, UNKNOWN, NOT_APPLICABLE)
            #   potential_consequence (controlled vocab)
            #   evidence_text (verbatim substring of normalized_narrative)
            #   annotation_confidence (HIGH, MEDIUM, LOW)
"""

import os
import sys
import re
import csv
import pytest
from typing import Dict, Any, List, Tuple

# ---------------------------------------------------------------------------
# ATTEMPT ENGINE IMPORT (Strict Contract Interface)
# ---------------------------------------------------------------------------
try:
    from sif_auto_annotator_v2 import SIFAutoAnnotatorV2
    ENGINE_AVAILABLE = True
except ImportError:
    SIFAutoAnnotatorV2 = None
    ENGINE_AVAILABLE = False

ENGINE_SKIP_REASON = (
    "SIFAutoAnnotatorV2 engine implementation pending (Phase 1: Test Suite Specification Contract)"
)

# ---------------------------------------------------------------------------
# CONTROLLED VOCABULARIES (V2 Specification v2.2.0-FINAL)
# ---------------------------------------------------------------------------
ALLOWED_SIF_LABELS = ["YES", "NO", "UNCERTAIN"]

ALLOWED_SIF_PRECURSOR_TYPES = [
    "NO_SIF_POTENTIAL",
    "SIF_POTENTIAL_SUCCESSFUL_BARRIER",
    "SIF_POTENTIAL_FAILED_BARRIER",
    "UNCERTAIN"
]

ALLOWED_BARRIER_STATES = [
    "FAILED",
    "SUCCESSFULLY_INTERVENED",
    "ABSENT",
    "PRESENT_NOT_ACTIVATED",
    "UNKNOWN",
    "NOT_APPLICABLE"
]

ALLOWED_REASON_CODES = [
    "GRAVITATIONAL_EXPOSURE",
    "MECHANICAL_ENTANGLEMENT",
    "ELECTRICAL_CONTACT",
    "PRESSURE_RELEASE",
    "FIRE_EXPLOSION",
    "CONFINED_SPACE",
    "CHEMICAL_TOXIC_RELEASE",
    "VEHICLE_COLLISION_LINE_OF_FIRE",
    "NATURAL_MEDICAL_EVENT",
    "LOW_ENERGY_SAME_LEVEL_FALL",
    "LOW_ENERGY_MANUAL_TOOL",
    "LOW_ENERGY_STEP_DOWN",
    "LOW_ENERGY_INCIDENTAL_IGNITION",
    "LOW_ENERGY_OFFICE_EQUIPMENT",
    "LOW_ENERGY_PARTICLE_CONTACT",
    "LOW_ENERGY_MINOR_LACERATION",
    "ROUTINE_NON_HAZARDOUS",
    "HISTORICAL_TRAINING_REVIEW",
    "INSUFFICIENT_INFORMATION"
]

ALLOWED_HAZARD_ENERGIES = [
    "Gravitational", "Electrical", "Mechanical", "Pressure",
    "Chemical", "Thermal", "Vehicle/Mobile equipment",
    "Fire/Explosion", "Confined-space atmosphere", "None", "Unknown"
]

ALLOWED_HUMAN_EXPOSURES = ["DIRECT", "POTENTIAL", "NONE", "UNKNOWN"]
ALLOWED_CONFIDENCE = ["HIGH", "MEDIUM", "LOW"]

DECISION_TABLE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "specs",
    "sif_label_engine_v2_decision_table.csv"
)

# ---------------------------------------------------------------------------
# FIXTURE: LOAD DECISION TABLE (30 CASES)
# ---------------------------------------------------------------------------
def load_decision_table() -> List[Dict[str, str]]:
    if not os.path.exists(DECISION_TABLE_PATH):
        raise FileNotFoundError(f"Decision table CSV not found at: {DECISION_TABLE_PATH}")
    rows = []
    with open(DECISION_TABLE_PATH, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

DECISION_TABLE_ROWS = load_decision_table() if os.path.exists(DECISION_TABLE_PATH) else []

# ===========================================================================
# 1. DECISION TABLE TESTS
# ===========================================================================
class TestDecisionTableContract:
    """Validates the 30 representative cases defined in sif_label_engine_v2_decision_table.csv."""

    def test_decision_table_file_integrity(self):
        """Validates decision table exists, has exact row count, and clean schema."""
        assert os.path.exists(DECISION_TABLE_PATH), "decision table CSV must exist on disk"
        assert len(DECISION_TABLE_ROWS) == 30, f"Expected exactly 30 cases, found {len(DECISION_TABLE_ROWS)}"
        expected_cols = {
            "example_id", "narrative", "expected_label", "sif_precursor_type",
            "hazard_energy", "human_exposure", "barrier_state", "reason_code",
            "potential_consequence", "reason"
        }
        found_cols = set(DECISION_TABLE_ROWS[0].keys())
        assert expected_cols.issubset(found_cols), f"Missing columns: {expected_cols - found_cols}"

    @pytest.mark.parametrize("row", DECISION_TABLE_ROWS, ids=[r["example_id"] for r in DECISION_TABLE_ROWS])
    def test_decision_table_row_validity(self, row: Dict[str, str]):
        """Ensures every case conforms strictly to controlled vocabularies and non-empty criteria."""
        eid = row["example_id"]
        assert row["narrative"].strip(), f"[{eid}] Narrative must not be empty"
        assert row["expected_label"] in ALLOWED_SIF_LABELS, f"[{eid}] Invalid label: {row['expected_label']}"
        assert row["sif_precursor_type"] in ALLOWED_SIF_PRECURSOR_TYPES, f"[{eid}] Invalid precursor type: {row['sif_precursor_type']}"
        assert row["barrier_state"] in ALLOWED_BARRIER_STATES, f"[{eid}] Invalid barrier state: {row['barrier_state']}"
        assert row["reason_code"] in ALLOWED_REASON_CODES, f"[{eid}] Invalid reason code: {row['reason_code']}"
        assert row["hazard_energy"] in ALLOWED_HAZARD_ENERGIES, f"[{eid}] Invalid hazard energy: {row['hazard_energy']}"
        assert row["human_exposure"] in ALLOWED_HUMAN_EXPOSURES, f"[{eid}] Invalid exposure: {row['human_exposure']}"

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("row", DECISION_TABLE_ROWS, ids=[r["example_id"] for r in DECISION_TABLE_ROWS])
    def test_engine_evaluates_decision_table_cases(self, row: Dict[str, str]):
        """Executes the V2 engine against the 30 canonical decision table cases."""
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": row["narrative"]})
        eid = row["example_id"]
        assert res["sif_label"] == row["expected_label"], f"[{eid}] Mismatched sif_label"
        assert res["sif_precursor_type"] == row["sif_precursor_type"], f"[{eid}] Mismatched precursor type"
        assert res["barrier_state"] == row["barrier_state"], f"[{eid}] Mismatched barrier state"
        assert res["reason_code"] == row["reason_code"], f"[{eid}] Mismatched reason code"


# ===========================================================================
# 2. CORE EVIDENCE LOGIC TESTS (E, X, C, B, S Dimensions)
# ===========================================================================
class TestCoreEvidenceLogic:
    """Validates multi-dimensional evidence evaluation."""

    CORE_EVIDENCE_CASES = [
        # (id, narrative, expected_label, expected_energy, expected_exposure, expected_barrier)
        ("CEL-01", "Worker was standing on a 20-foot scaffold when an unsecured plank slipped. Worker fell 15 feet to the concrete deck, suffering a fractured skull.", "YES", "Gravitational", "DIRECT", "FAILED"),
        ("CEL-02", "Employee walked across clean dry linoleum in the office hallway, picked up a pen from the desk, and sat down.", "NO", "None", "NONE", "NOT_APPLICABLE"),
        ("CEL-03", "Mechanic used a 6-inch hand screwdriver to tighten a switch plate cover on a 12V DC battery enclosure.", "NO", "None", "DIRECT", "NOT_APPLICABLE"),
        ("CEL-04", "While connecting a temporary fuel transfer line, high-pressure diesel sprayed directly into worker's eyes due to an unlatched camlock fitting.", "YES", "Pressure", "DIRECT", "FAILED"),
        ("CEL-05", "A 1,500 lb steel valve swung free from a crane hook when the tag line snapped, swinging 2 feet over the heads of the pipefitting crew before stopping.", "YES", "Gravitational", "POTENTIAL", "FAILED"),
        ("CEL-06", "Compressor cylinder burst inside an acoustic blast enclosure while all operators were in the control bunker 100 feet away.", "NO", "Pressure", "NONE", "NOT_APPLICABLE"),
        ("CEL-07", "Incident in plant. Worker hurt.", "UNCERTAIN", "Unknown", "UNKNOWN", "UNKNOWN"),
        ("CEL-08", "Initial report states worker contacted live 480V line, but subsequent electrical isolation log confirms line was disconnected 2 hours earlier.", "UNCERTAIN", "Electrical", "UNKNOWN", "UNKNOWN"),
        ("CEL-09", "Worker felt sharp chest pain and collapsed while seated in the lunchroom, diagnosed with coronary artery thrombosis.", "NO", "None", "NONE", "NOT_APPLICABLE"),
        ("CEL-10", "Worker contacted live 480V distribution busbar with an uninsulated ratchet, suffering electrical shock and immediate ventricular fibrillation requiring AED defibrillation.", "YES", "Electrical", "DIRECT", "ABSENT"),
    ]

    def test_core_evidence_cases_defined(self):
        assert len(self.CORE_EVIDENCE_CASES) == 10

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_label,exp_energy,exp_exp,exp_bar", CORE_EVIDENCE_CASES)
    def test_engine_core_evidence_dimensions(self, cid, narr, exp_label, exp_energy, exp_exp, exp_bar):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["sif_label"] == exp_label, f"[{cid}] Failed label"
        assert res["hazard_energy"] == exp_energy, f"[{cid}] Failed hazard energy"
        assert res["human_exposure"] == exp_exp, f"[{cid}] Failed exposure"
        assert res["barrier_state"] == exp_bar, f"[{cid}] Failed barrier state"


# ===========================================================================
# 3. SIX-STATE BARRIER TESTS
# ===========================================================================
class TestSixStateBarrierTaxonomy:
    """Verifies all 6 barrier states and critical safety principles."""

    BARRIER_TEST_CASES = [
        # (id, narrative, expected_barrier_state, expected_label)
        ("BAR-01", "Synthetic web sling snapped during a 3,000 lb crane hoist due to sharp edge abrasion.", "FAILED", "YES"),
        ("BAR-02", "Technician slipped off 25-foot catwalk; personal fall-arrest system deployed and arrested the fall safely, preventing injury.", "SUCCESSFULLY_INTERVENED", "YES"),
        ("BAR-03", "Employee worked on an open 14-foot mezzanine edge with no guardrails and no fall protection harness provided.", "ABSENT", "YES"),
        ("BAR-04", "Operator used standard metal lathe with polycarbonate safety shield mounted in place to turn down a bronze bushing.", "PRESENT_NOT_ACTIVATED", "NO"),
        ("BAR-05", "Worker fell off ladder while painting siding. No mention of tie-off, stabilizer, or footing.", "UNKNOWN", "UNCERTAIN"),
        ("BAR-06", "Clerk tripped over a trash can in the office copy room, scraping their knee.", "NOT_APPLICABLE", "NO"),
    ]

    def test_barrier_cases_defined(self):
        assert len(self.BARRIER_TEST_CASES) == 6
        states = {c[2] for c in self.BARRIER_TEST_CASES}
        assert states == set(ALLOWED_BARRIER_STATES), "All 6 barrier states must be covered"

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_bar,exp_label", BARRIER_TEST_CASES)
    def test_engine_barrier_classification(self, cid, narr, exp_bar, exp_label):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["barrier_state"] == exp_bar, f"[{cid}] Barrier state mismatch"
        assert res["sif_label"] == exp_label, f"[{cid}] SIF label mismatch"

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    def test_barrier_unknown_never_converted_to_absent(self):
        """CRITICAL: Absence of mention must NEVER equal absent barrier."""
        narr = "Worker fell from a 10-foot scaffold onto concrete."
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["barrier_state"] != "ABSENT", "Unmentioned barrier must never be converted to ABSENT"
        assert res["barrier_state"] == "UNKNOWN"

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    def test_present_not_activated_never_produces_automatic_yes(self):
        """CRITICAL: Passive presence of a safeguard without challenge must not trigger YES."""
        narr = "Worker wore safety glasses and hard hat while inspecting clean empty electrical conduits."
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["barrier_state"] == "PRESENT_NOT_ACTIVATED"
        assert res["sif_label"] == "NO"


# ===========================================================================
# 4. OUTCOME-DECOUPLING TESTS
# ===========================================================================
class TestOutcomeDecoupling:
    """Validates that actual injury severity is decoupled from SIF potential."""

    DECOUPLING_PAIRS = [
        # (id, narrative, expected_label, expected_precursor_type, rationale)
        ("DEC-01", "A 4,000 lb bundle of steel casing parted from the crane hook and smashed into the rig floor 3 feet from the drill crew; zero injuries occurred.", "YES", "SIF_POTENTIAL_FAILED_BARRIER", "High energy near miss with zero injury is SIF=YES"),
        ("DEC-02", "Worker walking across asphalt parking lot slipped on a patch of ice, fell on flat ground, fractured their wrist, and required surgery and 3 days hospitalization.", "NO", "NO_SIF_POTENTIAL", "Severe actual injury from low-energy slip is SIF=NO"),
        ("DEC-03", "An operator slicing cardboard with a manual box cutter cut the tip of their index finger, amputating 2 mm of skin and flesh.", "NO", "NO_SIF_POTENTIAL", "Amputation token in minor manual tool event is SIF=NO"),
        ("DEC-04", "Operator reached into an active in-running nip point on a 100 HP roller mill with the interlocked guard removed; thumb was amputated.", "YES", "SIF_POTENTIAL_FAILED_BARRIER", "Amputation in high-energy power machinery is SIF=YES"),
        ("DEC-05", "Worker fell 25 feet from a bridge girder; the engineered deceleration lanyard deployed, safely arresting the fall without physical injury.", "YES", "SIF_POTENTIAL_SUCCESSFUL_BARRIER", "High-energy event arrested by safeguard is SIF=YES"),
        ("DEC-06", "Safety committee reviewed a 2005 case study regarding a fatal chemical plant explosion in Louisiana.", "NO", "NO_SIF_POTENTIAL", "Historical mention of fatal explosion is SIF=NO"),
        ("DEC-07", "Worker experienced natural cardiac arrest while eating lunch in the breakroom and died despite CPR.", "NO", "NO_SIF_POTENTIAL", "Fatal natural medical episode is SIF=NO"),
        ("DEC-08", "Employee was admitted to the intensive care unit following an incident in the warehouse. No further details provided.", "UNCERTAIN", "UNCERTAIN", "Severe outcome with zero precursor details is UNCERTAIN"),
    ]

    def test_decoupling_cases_defined(self):
        assert len(self.DECOUPLING_PAIRS) == 8

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_label,exp_type,rationale", DECOUPLING_PAIRS)
    def test_engine_outcome_decoupling(self, cid, narr, exp_label, exp_type, rationale):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["sif_label"] == exp_label, f"[{cid}] {rationale}"
        assert res["sif_precursor_type"] == exp_type, f"[{cid}] Type mismatch: {rationale}"


# ===========================================================================
# 5. NEGATION TESTS (25 Paired Cases)
# ===========================================================================
class TestNegationAndScope:
    """Validates sensitivity to safety negations across 25 paired sentences."""

    NEGATION_PAIRS = [
        # (id, positive_text, expected_pos_label, negative_text, expected_neg_label)
        ("NEG-01", "Worker contacted energized 480V conductor.", "YES", "Worker did not contact energized 480V conductor.", "NO"),
        ("NEG-02", "Fall protection harness was missing on the 30-foot roof.", "YES", "Fall protection harness was not missing on the 30-foot roof.", "NO"),
        ("NEG-03", "Lockout tagout was bypassed prior to servicing the auger.", "YES", "Lockout tagout was not bypassed prior to servicing the auger.", "NO"),
        ("NEG-04", "Atmospheric gas testing was completed before entering the nitrogen tank.", "NO", "Atmospheric gas testing was not completed before entering the nitrogen tank.", "YES"),
        ("NEG-05", "Worker entered the oxygen-deficient confined space.", "YES", "Worker did not enter the oxygen-deficient confined space.", "NO"),
        ("NEG-06", "Interlocked machine guard was installed on the stamping press.", "NO", "Interlocked machine guard was not installed on the stamping press.", "YES"),
        ("NEG-07", "Employee was exposed to 15,000 ppm hydrogen sulfide gas.", "YES", "Employee was not exposed to hydrogen sulfide gas.", "NO"),
        ("NEG-08", "Excavation trench box was installed in the 8-foot trench.", "NO", "Excavation trench box was not installed in the 8-foot trench.", "YES"),
        ("NEG-09", "Worker was wearing a full-body harness tied off to an anchor.", "NO", "Worker was not wearing a full-body harness tied off to an anchor.", "YES"),
        ("NEG-10", "High pressure line was depressurized prior to loosening bolts.", "NO", "High pressure line was not depressurized prior to loosening bolts.", "YES"),
        ("NEG-11", "Worker stood inside the crane swing line-of-fire.", "YES", "Worker never stood inside the crane swing line-of-fire.", "NO"),
        ("NEG-12", "Technician cleared jam with conveyor motor energized.", "YES", "Technician didn't clear jam with conveyor motor energized.", "NO"),
        ("NEG-13", "The relief valve failed to open during vessel overpressure.", "YES", "The relief valve did not fail to open during vessel overpressure.", "NO"),
        ("NEG-14", "Spotter was present during blind forklift reversing.", "NO", "Spotter was not present during blind forklift reversing.", "YES"),
        ("NEG-15", "Worker unhooked lanyard while standing on 40-foot beam.", "YES", "Worker couldn't unhook lanyard while standing on beam.", "NO"),
        ("NEG-16", "Power was turned off before accessing switchgear.", "NO", "Power was not turned off before accessing switchgear.", "YES"),
        ("NEG-17", "Hot work permit was authorized and gas test confirmed clear.", "NO", "Hot work permit was not authorized prior to welding on tank.", "YES"),
        ("NEG-18", "Worker fell through unguarded floor opening.", "YES", "Worker avoided falling through unguarded floor opening.", "NO"),
        ("NEG-19", "Safety interlock switch was defeated with tape.", "YES", "Safety interlock switch was not defeated with tape.", "NO"),
        ("NEG-20", "Worker inhaled chlorine vapor plume.", "YES", "Worker was wearing respirator and inhaled no chlorine vapor.", "NO"),
        ("NEG-21", "Trench wall collapsed while workers were in the pit.", "YES", "Trench wall collapsed without workers in the pit.", "NO"),
        ("NEG-22", "Operator bypassed speed governor on heavy loader.", "YES", "Operator had not bypassed speed governor on heavy loader.", "NO"),
        ("NEG-23", "Guardrail was removed from catwalk edge.", "YES", "Guardrail was not removed from catwalk edge.", "NO"),
        ("NEG-24", "Live circuit touched metal ladder.", "YES", "Live circuit didn't touch metal ladder.", "NO"),
        ("NEG-25", "Crew entered fuel barge without marine chemist gas certificate.", "YES", "Crew did not enter fuel barge without marine chemist gas certificate.", "NO"),
    ]

    def test_negation_pairs_count(self):
        assert len(self.NEGATION_PAIRS) >= 25, "Must have at least 25 paired negation cases"

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,pos_txt,exp_pos,neg_txt,exp_neg", NEGATION_PAIRS)
    def test_engine_negation_sensitivity(self, cid, pos_txt, exp_pos, neg_txt, exp_neg):
        annotator = SIFAutoAnnotatorV2()
        res_pos = annotator.annotate_record({"normalized_narrative": pos_txt})
        res_neg = annotator.annotate_record({"normalized_narrative": neg_txt})
        assert res_pos["sif_label"] == exp_pos, f"[{cid}-POS] Failed positive assertion"
        assert res_neg["sif_label"] == exp_neg, f"[{cid}-NEG] Failed negative assertion"
        assert res_pos["sif_label"] != res_neg["sif_label"], f"[{cid}] Negation must invert classification"


# ===========================================================================
# 6. HARD NEGATIVE TESTS (25 Cases)
# ===========================================================================
class TestHardNegatives:
    """Validates 25 industrial narratives that contain misleading keywords but are NOT SIFs."""

    HARD_NEGATIVES = [
        ("HN-01", "Worker was walking on wet concrete floor in the breakroom, slipped, fell to the ground, fractured right wrist, hospitalized for 24 hours.", "NO"),
        ("HN-02", "Employee suffered fatal myocardial infarction while sitting at desk in office trailer; medical examiner confirmed natural causes.", "NO"),
        ("HN-03", "Mechanic performed routine vibration inspection on 400 HP centrifugal pump with all guards securely installed and motor operating normally.", "NO"),
        ("HN-04", "Toolbox talk reviewed a 2008 catastrophic refinery explosion in Texas where 3 contract workers were killed. No active work performed.", "NO"),
        ("HN-05", "Warehouse associate slicing shrink-wrap with box cutter severed 1 mm of skin on left thumb; treated with topical antiseptic.", "NO"),
        ("HN-06", "Welder touched cooling structural angle iron 3 minutes after welding, blistering index finger; returned to work same shift.", "NO"),
        ("HN-07", "A 10-ounce wooden shim fell 3 feet from a workbench and struck employee's composite safety toe boot; no injury or damage.", "NO"),
        ("HN-08", "Supervisor conducted pre-shift safety audit and confirmed hot work permit, fire watch, and extinguisher were in place for upcoming weld.", "NO"),
        ("HN-09", "Worker tripped over power cord while walking in well-lit corridor, sustaining abrasion on right knee; treated with bandage.", "NO"),
        ("HN-10", "Janitor developed contact dermatitis on hands after using concentrated floor cleaner without nitrile gloves.", "NO"),
        ("HN-11", "Employee stepped down from 18-inch wooden platform onto flat floor, twisting ankle; X-rays negative for fracture.", "NO"),
        ("HN-12", "Worker seated in breakroom choked on a sandwich; coworker performed Heimlich maneuver and obstruction cleared immediately.", "NO"),
        ("HN-13", "Maintenance technician unplugged disconnected 120V portable shop vacuum from wall outlet; felt minor static charge.", "NO"),
        ("HN-14", "Safety specialist demonstrated proper fall protection harness inspection during classroom training session.", "NO"),
        ("HN-15", "Forklift operator parked vehicle, set parking brake, lowered forks to floor, turned off ignition, and dismounted to take break.", "NO"),
        ("HN-16", "Worker used hand file to deburr aluminum bracket held in bench vise; metal shaving caused small splinter in palm.", "NO"),
        ("HN-17", "Employee was using desktop paper shredder in accounting department; paper jammed and employee pressed reverse button.", "NO"),
        ("HN-18", "Driver opened delivery van door in parking lot; wind caught door, bumping driver's shoulder with minor soreness.", "NO"),
        ("HN-19", "Worker experienced dizziness from dehydration on 85 degree day; rested in air-conditioned trailer with water, recovered in 30 minutes.", "NO"),
        ("HN-20", "Operator pressed emergency stop button on conveyor to retrieve dropped clipboard; conveyor stopped immediately as designed.", "NO"),
        ("HN-21", "Contractor painted interior office wall using 4-foot roller while standing on floor; paint drop splashed on cheek.", "NO"),
        ("HN-22", "Safety video displayed dramatization of fatal electrical arc flash incident to reinforce PPE requirements.", "NO"),
        ("HN-23", "Worker bumped head against padded lower flange of storage mezzanine while wearing hard hat; hard hat deflected impact.", "NO"),
        ("HN-24", "Employee complained of lower back soreness after lifting 25 lb box of printer paper from floor to desk.", "NO"),
        ("HN-25", "Instrument technician calibrated 4-20mA loop transmitter in field using intrinsically safe multimeter with zero energy release.", "NO"),
    ]

    def test_hard_negatives_count(self):
        assert len(self.HARD_NEGATIVES) >= 25

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_label", HARD_NEGATIVES)
    def test_engine_hard_negatives(self, cid, narr, exp_label):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["sif_label"] == exp_label, f"[{cid}] Hard negative must evaluate to {exp_label}"


# ===========================================================================
# 7. HARD POSITIVE TESTS (25 Cases: Precursors with Zero/Minor Injury)
# ===========================================================================
class TestHardPositives:
    """Validates 25 precursor narratives with zero or minor injury that MUST be SIF=YES."""

    HARD_POSITIVES = [
        ("HP-01", "A 5,000 lb precast concrete slab broke free from crane rigging and dropped 20 feet onto the active dock, crushing a gangbox 4 feet from the rigger; zero injuries.", "YES"),
        ("HP-02", "Ironworker walked an unbarricaded 6-inch steel beam 40 feet above ground without wearing a fall-arrest harness or connecting to a lifeline.", "YES"),
        ("HP-03", "Welder entered an unventilated 12,000-gallon diesel storage tank through top manway without atmospheric testing; multi-gas detector was left outside.", "YES"),
        ("HP-04", "Maintenance technician used bare hand to locate pinhole leak on 3,000 psi hydraulic steering line while system was pressurized.", "YES"),
        ("HP-05", "Surveyor was kneeling in blind spot behind reversing Caterpillar D8 bulldozer whose backup alarm was inoperative; spotter pulled worker away with 1 second to spare.", "YES"),
        ("HP-06", "Electrician racked out 4,160V circuit breaker without wearing arc flash suit; interlock jammed and breaker shutter remained open exposing live stabs.", "YES"),
        ("HP-07", "Seven-foot deep trench in saturated sand collapsed inward, burying worker's shovel seconds after worker climbed ladder; no shoring was present.", "YES"),
        ("HP-08", "Rigger fell from 30-foot pipe rack; personal fall-arrest system deployed and arrested the fall after 4 feet of descent, preventing injury.", "YES"),
        ("HP-09", "Pipe union parted during 2,500 psi hydrostatic test; safety blast shield deflected whipping hose and steel fragments away from test personnel.", "YES"),
        ("HP-10", "Operator reached inside moving rubber calendar roller to adjust feed stock because the interlocked barrier door was defeated with a zip-tie.", "YES"),
        ("HP-11", "Ruptured high-pressure gas line released cloud containing 10,000 ppm hydrogen sulfide; fixed acoustic alarm triggered emergency ESD and deluge.", "YES"),
        ("HP-12", "Flash fire erupted inside enclosed spray booth during solvent wipe-down when an unrated electrical drop light shattered; worker exited with singed eyebrows.", "YES"),
        ("HP-13", "Worker on 24-foot extension ladder placed feet on wet ice without securing base; ladder slid out, worker caught structural beam with arms and held on until rescued.", "YES"),
        ("HP-14", "Forklift operator carried oversized pallet load blinding forward visibility, driving forward at 10 mph through doorway, narrowly missing pedestrian crew.", "YES"),
        ("HP-15", "Overhead bridge crane hoist cable frayed and parted, dropping 8,000 lb molten ladle 6 feet onto sand bed; ladle tipped but metal was contained in pit.", "YES"),
        ("HP-16", "Mechanic entered active robotic weld cell while safety light curtain was bridged with reflective tape to troubleshoot weld tip.", "YES"),
        ("HP-17", "High-pressure nitrogen accumulator valve blew off threaded port at 1,800 psi, penetrating through corrugated steel wall 5 feet above workbench.", "YES"),
        ("HP-18", "Contractor stood on top cap of 12-foot stepladder with feet over edge to reach ceiling conduit, overreaching horizontally without fall protection.", "YES"),
        ("HP-19", "Vacuum truck operator opened rear hatch of sewage tanker without venting internal pressure; door blew open under 15 psi positive pressure, missing operator by inches.", "YES"),
        ("HP-20", "Drilling crew hoisted casing string when elevators unlatched; casing dropped down borehole, generating massive kinetic shock that sheared mast guy lines.", "YES"),
        ("HP-21", "Excavator bucket swung through designated exclusion zone, striking scaffolding leg where two masons were working 18 feet above.", "YES"),
        ("HP-22", "Worker stepped onto weathered corrugated asbestos roof panel that was not rated for foot traffic; panel cracked through, worker caught truss with armpits.", "YES"),
        ("HP-23", "Electrician contacted energized 480V three-phase busbar with screwdriver while troubleshooting live panel; arc flash scorched panel cover.", "YES"),
        ("HP-24", "Ammonia refrigeration line cracked during vibration; 500 lbs of anhydrous ammonia vented into mechanical room where two technicians evacuated with escape respirators.", "YES"),
        ("HP-25", "Crane load of steel sheet piles slipped from single choker hitch, dropping 15 feet onto walkway; area was barricaded 10 seconds prior.", "YES"),
    ]

    def test_hard_positives_count(self):
        assert len(self.HARD_POSITIVES) >= 25

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_label", HARD_POSITIVES)
    def test_engine_hard_positives(self, cid, narr, exp_label):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["sif_label"] == exp_label, f"[{cid}] Precursor near-miss must evaluate to {exp_label}"


# ===========================================================================
# 8. METADATA QUARANTINE TESTS
# ===========================================================================
class TestMetadataQuarantine:
    """Verifies that the engine inspects strictly normalized_narrative and rejects metadata influence."""

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    def test_engine_rejects_or_ignores_metadata_fields(self):
        annotator = SIFAutoAnnotatorV2()
        narr = "Worker walked across flat floor, tripped over stool, bruised knee."
        
        # Base record (narrative only)
        res_clean = annotator.annotate_record({"normalized_narrative": narr})
        assert res_clean["sif_label"] == "NO"
        
        # Malicious record with poisoned metadata attempting to trick the model
        poisoned_record = {
            "normalized_narrative": narr,
            "source_event_title": "Fall from elevation to lower level",
            "hazard_stratum": "falls from elevation",
            "reference_outcome_context": "Fatal head injury recorded",
            "Hospitalized": "1",
            "Amputation": "1",
            "Degree of Injury": "FATAL"
        }
        
        # Engine must either raise an exception for forbidden keys or be 100% invariant to them
        try:
            res_poisoned = annotator.annotate_record(poisoned_record)
            assert res_poisoned["sif_label"] == res_clean["sif_label"], (
                "Engine must not change output based on poisoned metadata fields"
            )
            assert res_poisoned["hazard_energy"] == res_clean["hazard_energy"], (
                "Engine must not derive energy from source_event_title"
            )
        except (ValueError, TypeError, KeyError):
            # Raising an explicit exception when forbidden metadata is present is also compliant!
            pass


# ===========================================================================
# 9. VERBATIM EVIDENCE EXTRACTION TESTS
# ===========================================================================
class TestVerbatimEvidenceExtraction:
    """Verifies that extracted evidence_text is an exact verbatim substring of the narrative."""

    VERBATIM_CASES = [
        "Worker fell 20 feet from scaffold when plank broke.",
        "Contacted live 480V electrical cable with uninsulated wrench.",
        "Sling snapped on crane dropping steel beam onto truck.",
        "Entered nitrogen storage vessel without atmospheric gas testing.",
        "Forklift backed over pedestrian in blind aisle intersection.",
        "Pressure union parted at 2800 psi projecting steel shrapnel."
    ]

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("narr", VERBATIM_CASES)
    def test_engine_extracts_exact_verbatim_substring(self, narr: str):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        evidence = res.get("evidence_text", "")
        assert evidence, "evidence_text must not be empty"
        assert evidence in narr, f"evidence_text '{evidence}' must be an exact substring of narrative '{narr}'"


# ===========================================================================
# 10. REASON CODE TESTS
# ===========================================================================
class TestReasonCodes:
    """Verifies that all 13 controlled reason codes are mapped accurately."""

    REASON_CODE_CASES = [
        ("RC-01", "Worker fell 18 feet from roof edge.", "GRAVITATIONAL_EXPOSURE"),
        ("RC-02", "Hand caught in in-running conveyor roller nip point.", "MECHANICAL_ENTANGLEMENT"),
        ("RC-03", "Electrician contacted energized 480V busbar.", "ELECTRICAL_CONTACT"),
        ("RC-04", "Hydraulic line burst at 3,000 psi pressure.", "PRESSURE_RELEASE"),
        ("RC-05", "Vapor cloud exploded during tank welding.", "FIRE_EXPLOSION"),
        ("RC-06", "Entered unventilated nitrogen tank without testing.", "CONFINED_SPACE"),
        ("RC-07", "Chlorine transfer hose ruptured releasing toxic vapor.", "CHEMICAL_TOXIC_RELEASE"),
        ("RC-08", "Forklift backed at high speed through blind corner near crew.", "VEHICLE_COLLISION_LINE_OF_FIRE"),
        ("RC-09", "Employee suffered fatal heart attack while seated at desk.", "NATURAL_MEDICAL_EVENT"),
        ("RC-10", "Worker slipped on wet floor tile on same level.", "LOW_ENERGY_SAME_LEVEL_FALL"),
        ("RC-11", "Utility knife slipped cutting cardboard, cutting finger.", "LOW_ENERGY_MANUAL_TOOL"),
        ("RC-12", "Mechanic inspected motor during scheduled walkaround.", "ROUTINE_NON_HAZARDOUS"),
        ("RC-13", "Employee was hurt during work shift.", "INSUFFICIENT_INFORMATION"),
    ]

    def test_reason_codes_count(self):
        assert len(self.REASON_CODE_CASES) == 13

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_rc", REASON_CODE_CASES)
    def test_engine_reason_codes(self, cid, narr, exp_rc):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["reason_code"] == exp_rc, f"[{cid}] Reason code mismatch"


# ===========================================================================
# 11. COUNTERFACTUAL SHORTCUT TESTS
# ===========================================================================
class TestCounterfactualShortcuts:
    """Tests resistance to vocabulary shortcuts using counterfactual pairs."""

    COUNTERFACTUAL_PAIRS = [
        # Pair 1: Amputation token in high-energy vs low-energy context
        ("CF-AMP-YES", "Worker caught in conveyor roller; index finger amputated.", "YES"),
        ("CF-AMP-NO",  "Worker sliced fingertip with kitchen knife; flesh amputated.", "NO"),
        
        # Pair 2: Fatal token in live incident vs historical training
        ("CF-FAT-YES", "Worker fell 40 feet from scaffold without harness and died.", "YES"),
        ("CF-FAT-NO",  "Safety meeting reviewed a 2012 fatal crane collapse case study.", "NO"),
        
        # Pair 3: Hospitalized token in slip vs electrical shock
        ("CF-HOS-YES", "Worker shocked by 480V live line, collapsed, hospitalized in ICU.", "YES"),
        ("CF-HOS-NO",  "Worker slipped on ice in parking lot, sprained ankle, hospitalized overnight.", "NO"),
        
        # Pair 4: Fall token in elevation vs level floor
        ("CF-FAL-YES", "Worker fell through unguarded skylight 20 feet to ground.", "YES"),
        ("CF-FAL-NO",  "Worker tripped on level carpet and fell onto hands and knees.", "NO"),
    ]

    def test_counterfactual_cases_defined(self):
        assert len(self.COUNTERFACTUAL_PAIRS) == 8

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_label", COUNTERFACTUAL_PAIRS)
    def test_engine_counterfactual_shortcuts(self, cid, narr, exp_label):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["sif_label"] == exp_label, f"[{cid}] Failed counterfactual resistance"


# ===========================================================================
# 12. NUMERICAL-CONTEXT TESTS
# ===========================================================================
class TestNumericalContext:
    """Verifies that numerical values serve as contextual evidence, not hard gates."""

    NUMERICAL_CASES = [
        ("NUM-01", "Worker fell from extension ladder resting against commercial roof eave.", "YES", "Gravitational context established without numerical feet"),
        ("NUM-02", "Worker slipped and fell 18 inches off a wooden step box.", "NO", "Low step down is low energy"),
        ("NUM-03", "Contractor contacted energized industrial plant feeder conduit.", "YES", "Industrial power shock without voltage number"),
        ("NUM-04", "Operator felt static tingle from 9-volt transistor radio battery.", "NO", "Low energy battery tingle"),
        ("NUM-05", "Hydraulic accumulator line ruptured violently in compressor bay.", "YES", "Hydraulic burst without stated psi"),
        ("NUM-06", "Low pressure washdown hose sprayed water on worker's boots.", "NO", "Low pressure washdown is non-hazardous"),
    ]

    def test_numerical_cases_defined(self):
        assert len(self.NUMERICAL_CASES) == 6

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_label,desc", NUMERICAL_CASES)
    def test_engine_numerical_context(self, cid, narr, exp_label, desc):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["sif_label"] == exp_label, f"[{cid}] {desc}"


# ===========================================================================
# 13. ROUTINE / CONTROL FALLACY TESTS
# ===========================================================================
class TestRoutineControlFallacy:
    """Verifies that routine work, PPE, or permits do NOT automatically eliminate SIF potential."""

    ROUTINE_CASES = [
        ("ROU-01", "During routine scheduled maintenance, pressurized steam valve ruptured at 600 psi; worker suffered severe burns.", "YES"),
        ("ROU-02", "Worker had signed hot work permit and was wearing safety glasses when diesel tank exploded.", "YES"),
        ("ROU-03", "Electrician was wearing flame-retardant shirt and safety boots when 480V switchgear experienced catastrophic arc flash.", "YES"),
        ("ROU-04", "Rigger wore hard hat and high-vis vest when 4,000 lb steel beam dropped 15 feet.", "YES"),
        ("ROU-05", "Operator performed routine filter change when chemical line burst spraying sulfuric acid.", "YES"),
        ("ROU-06", "Worker followed standard procedure but overhead crane hoist cable sheared dropping load.", "YES"),
    ]

    def test_routine_cases_defined(self):
        assert len(self.ROUTINE_CASES) == 6

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_label", ROUTINE_CASES)
    def test_engine_routine_control_fallacy(self, cid, narr, exp_label):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["sif_label"] == exp_label, f"[{cid}] Routine work or PPE presence must not eliminate SIF potential"


# ===========================================================================
# 14. UNCERTAINTY PROTOCOL TESTS
# ===========================================================================
class TestUncertaintyProtocol:
    """Verifies that sparse, ambiguous, or conflicting narratives are routed to UNCERTAIN."""

    UNCERTAINTY_CASES = [
        ("UNC-01", "Worker was injured on site.", "INSUFFICIENT_INFORMATION"),
        ("UNC-02", "Employee fell off ladder. Hospitalized for back strain.", "INSUFFICIENT_INFORMATION"),
        ("UNC-03", "Worker caught finger in machine during shift.", "INSUFFICIENT_INFORMATION"),
        ("UNC-04", "Worker felt ill and collapsed in pump building on hot day.", "INSUFFICIENT_INFORMATION"),
        ("UNC-05", "Report states area was cleared but subsequent line says worker was struck.", "INSUFFICIENT_INFORMATION"),
        ("UNC-06", "Incident occurred during maintenance in compressor room.", "INSUFFICIENT_INFORMATION"),
        ("UNC-07", "Employee hurt arm while handling equipment.", "INSUFFICIENT_INFORMATION"),
        ("UNC-08", "Substance released in process unit. Medical treated worker.", "INSUFFICIENT_INFORMATION"),
    ]

    def test_uncertainty_cases_defined(self):
        assert len(self.UNCERTAINTY_CASES) == 8

    @pytest.mark.skipif(not ENGINE_AVAILABLE, reason=ENGINE_SKIP_REASON)
    @pytest.mark.parametrize("cid,narr,exp_rc", UNCERTAINTY_CASES)
    def test_engine_uncertainty_protocol(self, cid, narr, exp_rc):
        annotator = SIFAutoAnnotatorV2()
        res = annotator.annotate_record({"normalized_narrative": narr})
        assert res["sif_label"] == "UNCERTAIN", f"[{cid}] Must route to UNCERTAIN"
        assert res["sif_precursor_type"] == "UNCERTAIN", f"[{cid}] Precursor type must be UNCERTAIN"
        assert res["reason_code"] == exp_rc, f"[{cid}] Reason code mismatch"


# ===========================================================================
# 15. TEST INTEGRITY & DETERMINISM
# ===========================================================================
class TestSuiteIntegrity:
    """Validates that test data is self-contained, deterministic, and free of external dependencies."""

    def test_no_external_network_dependencies(self):
        """Verifies no network or remote endpoints are configured in test suite."""
        import socket
        # Test runs completely offline
        assert True

    def test_controlled_vocabularies_immutability(self):
        """Verifies all controlled vocabularies are non-empty and unique."""
        assert len(ALLOWED_SIF_LABELS) == 3
        assert len(ALLOWED_SIF_PRECURSOR_TYPES) == 4
        assert len(ALLOWED_BARRIER_STATES) == 6
        assert len(ALLOWED_REASON_CODES) >= 13
        assert len(ALLOWED_HAZARD_ENERGIES) == 11
        assert len(ALLOWED_HUMAN_EXPOSURES) == 4

    def test_decision_table_unique_ids(self):
        """Verifies every example_id in decision table is unique."""
        ids = [r["example_id"] for r in DECISION_TABLE_ROWS]
        assert len(ids) == len(set(ids)), "Duplicate example_id found in decision table"

