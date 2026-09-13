"""
tests/test_sif_engine_v23_bugfixes.py
======================================
Regression Test Suite for SIF Label Engine V2.3 Targeted Bugfixes (Phase 5.2).

Covers:
- BUG 1: Electrical Shock + Cardiac Arrest (preserves traumatic electrical pathway over secondary cardiac arrest)
- BUG 2: Pinch / Crush Vocabulary Gap (narrow semantic coverage for caught/pinned between/under equipment/structure)
- BUG 3: Pressure Release / Tire Inflation (narrow pressure release/burst/projectile coverage)
- BUG 4: Falling Load Regex False Positive (requires actual falling load relationship; excludes ground-level pallet trips)
"""

import pytest
from sif_auto_annotator_v23 import SIFAutoAnnotatorV23

@pytest.fixture(scope="module")
def annotator():
    return SIFAutoAnnotatorV23()

# =============================================================================
# BUG 1: Electrical Shock + Cardiac Arrest
# =============================================================================
@pytest.mark.parametrize("cid,narrative,exp_label,exp_reason", [
    (
        "HSE_220866149_3266",
        "On June 28, 2016, an employee was test drilling for sinkhole activity when contact was made with an overhead high voltage power line. A locally made drilling machine that did not have a model or serial number available for identification was used. The employee received electrical shock from contacting a 7,026 volt, overhead power line, receiving severe internal injuries. The employee then crawled five to six feet to escape the hazard, collapsed, and went into cardiac arrest. The employee never regained consciousness before dying from his injuries on July 7, 2016.",
        "YES",
        "ELECTRICAL_CONTACT"
    ),
    (
        "HSE_220876023_3195",
        "At 10:00 a.m. on July 14, 2016, an employee was working for a firm of plumbing, heating, and air conditioning contractors. He was disconnecting an air duct that led to an air handler. He was removing the screws from the duct work. There were no witnesses to what happened, but coworker found him unresponsive when the coworker returned to the scene of the incident. It was determined that the employee had come into contact with a loose wire from another source. The wire was energized and the employee had been electrocuted. He had gone into cardiac arrest.",
        "YES",
        "ELECTRICAL_CONTACT"
    ),
    (
        "HSE_220973358_1864",
        "At 2:00 p.m. on January 25, 2017, Employee #1 and a coworker were inspecting a newly installed resistor for the water pump within a cabinet of a 480 volt high frequency induction welder. Specifically, they were inspecting the resistor to determine why the newly replaced resistor was leaking water. The coworker replaced the resistor, removed the lock from the welder's power source, and ran the welder to see if the replacement of the resistor had stopped the water leak. However, his efforts were not successful. Just before the coworker's shift ended, he called Employee #1 over, who was starting his shift, to explain the problem and to ask that he continue work on the welder during his shift. With the welder running and the new resistor in place, Employee #1, for an unknown reason, moved closer to the inside of the welder's cabinet and came in contact with an energized part of the 480 volt welder. Employee #1 received an electrical shock to his right side, causing him to go into cardiac arrest. Emergency services were contacted and, upon arrival, were able to revive him. Employee #1 was taken to a nearby hospital where he was admitted and treated for third degree burns to his right arm and the right side of his abdomen.",
        "YES",
        "ELECTRICAL_CONTACT"
    ),
    (
        "B1_NEG_01",
        "A worker collapsed in the breakroom from cardiac arrest due to a pre-existing coronary artery condition.",
        "NO",
        "NATURAL_MEDICAL_EVENT"
    )
])
def test_bug1_electrical_cardiac(annotator, cid, narrative, exp_label, exp_reason):
    res = annotator.annotate_narrative(narrative)
    assert res["sif_label"] == exp_label, f"[{cid}] Expected {exp_label}, got {res['sif_label']}"
    assert res["reason_code"] == exp_reason, f"[{cid}] Expected {exp_reason}, got {res['reason_code']}"


# =============================================================================
# BUG 2: Pinch / Crush Vocabulary Gap
# =============================================================================
@pytest.mark.parametrize("cid,narrative,exp_label,exp_reason", [
    (
        "B2_POS_01",
        "An employee was caught between two heavy machines during plant maintenance.",
        "YES",
        "MECHANICAL_ENTANGLEMENT"
    ),
    (
        "B2_POS_02",
        "A technician was pinned between industrial equipment and the concrete wall structure.",
        "YES",
        "MECHANICAL_ENTANGLEMENT"
    ),
    (
        "B2_POS_03",
        "A worker was pinned under heavy machinery when the hydraulic support failed.",
        "YES",
        "MECHANICAL_ENTANGLEMENT"
    ),
    (
        "HSE_220794408_4727",
        "As Heat Inductor #2 moved to the resting position, Employee #1 became caught between Heat Inductors #1 and #2. Employee #1 was killed from total body blunt force trauma resulting from being crushed between Heat Inductors #1 and #2.",
        "YES",
        "MECHANICAL_ENTANGLEMENT"
    ),
    (
        "HSE_220842082_3732",
        "An employee working as a deckhand securing a barge to a barge dock was caught between the barge dock rake and the coaming of the barge. The employee was crushed and killed.",
        "YES",
        "MECHANICAL_ENTANGLEMENT"
    ),
    (
        "HSE_220865042_3292",
        "An employee was installing insulation on duct work from a scissor lift. The employee was pinned between the railing of the scissor lift and the upper mezzanine floor. The employee was killed from crushing injuries.",
        "YES",
        "MECHANICAL_ENTANGLEMENT"
    ),
    (
        "B2_NEG_01",
        "An employee was walking between two buildings when taking a rest break.",
        "NO",
        "ROUTINE_NON_HAZARDOUS"
    ),
    (
        "B2_NEG_02",
        "The safety meeting was scheduled between 12:00 p.m. and 1:00 p.m. in the lunchroom.",
        "UNCERTAIN",
        "INSUFFICIENT_INFORMATION"
    )
])
def test_bug2_pinch_crush(annotator, cid, narrative, exp_label, exp_reason):
    res = annotator.annotate_narrative(narrative)
    assert res["sif_label"] == exp_label, f"[{cid}] Expected {exp_label}, got {res['sif_label']}"
    assert res["reason_code"] == exp_reason, f"[{cid}] Expected {exp_reason}, got {res['reason_code']}"


# =============================================================================
# BUG 3: Pressure Release / Tire Inflation
# =============================================================================
@pytest.mark.parametrize("cid,narrative,exp_label,exp_reason", [
    (
        "B3_POS_01",
        "A worker was inflating a truck tire when the pressurized tire burst into fragments, striking him.",
        "YES",
        "PRESSURE_RELEASE"
    ),
    (
        "B3_POS_02",
        "High air pressure released during testing, causing a steel pipe valve projectile to strike a coworker.",
        "YES",
        "PRESSURE_RELEASE"
    ),
    (
        "HSE_220781348_4788",
        "At approximately 5:15 p.m. on July 15, 2015, Employee #1 was inflating a truck tire. The air pressure released and caused the tire to go airborne. Employee #1 was struck in the head by the truck tire projectile, and was killed from a massive head trauma.",
        "YES",
        "PRESSURE_RELEASE"
    ),
    (
        "SIR_968503",
        "An employee was changing a Dayton-style wheel. While removing the lugs, the employee hit the tire with a hammer and loosened the wheel. As the employee removed the last nut, the tire blew out, becoming a projectile that hit the employee in the face.",
        "YES",
        "PRESSURE_RELEASE"
    ),
    (
        "B3_NEG_01",
        "An employee checked tire pressure with a handheld gauge during a routine pre-trip vehicle inspection.",
        "UNCERTAIN",
        "INSUFFICIENT_INFORMATION"
    ),
    (
        "B3_NEG_02",
        "A worker operated an air hose under normal air pressure to blow dust off a workbench.",
        "UNCERTAIN",
        "INSUFFICIENT_INFORMATION"
    )
])
def test_bug3_pressure_tire(annotator, cid, narrative, exp_label, exp_reason):
    res = annotator.annotate_narrative(narrative)
    assert res["sif_label"] == exp_label, f"[{cid}] Expected {exp_label}, got {res['sif_label']}"
    assert res["reason_code"] == exp_reason, f"[{cid}] Expected {exp_reason}, got {res['reason_code']}"


# =============================================================================
# BUG 4: Falling Load Regex False Positive
# =============================================================================
@pytest.mark.parametrize("cid,narrative,exp_label,exp_reason", [
    (
        "B4_POS_01",
        "A suspended pallet fell from the crane and struck the worker on the shoulder.",
        "YES",
        "GRAVITATIONAL_EXPOSURE"
    ),
    (
        "SIR_1155722",
        "On 11/13/2016, an employee was conducting preventative maintenance when his upper back was struck by a falling wooden pallet.",
        "YES",
        "GRAVITATIONAL_EXPOSURE"
    ),
    (
        "B4_NEG_01",
        "A worker tripped over a nearby pallet and fell to the floor, injuring his wrist.",
        "UNCERTAIN",
        "INSUFFICIENT_INFORMATION"
    ),
    (
        "SIR_1166633",
        "An employee was transferring small packages of material from a conveyor to a cart when his foot was caught on the corner of a nearby pallet. He tripped and fell to the floor, fracturing his right arm and elbow.",
        "UNCERTAIN",
        "INSUFFICIENT_INFORMATION"
    )
])
def test_bug4_falling_load(annotator, cid, narrative, exp_label, exp_reason):
    res = annotator.annotate_narrative(narrative)
    assert res["sif_label"] == exp_label, f"[{cid}] Expected {exp_label}, got {res['sif_label']}"
    assert res["reason_code"] == exp_reason, f"[{cid}] Expected {exp_reason}, got {res['reason_code']}"

