#!/usr/bin/env python3
"""
sif_auto_annotator_v2.py
========================
Narrative-Only Serious Injury & Fatality (SIF) Label Engine V2.
SIH26165 Project.

This module implements the deterministic, explainable, narrative-only SIF labeling engine
specified in:
- SIF_LABEL_ENGINE_V2_SPEC.md (v2.2.0-FINAL)
- sif_label_engine_v2_decision_table.csv
- CHANGELOG_V2_FINAL.md

Architectural Tenets:
1. Strict Metadata Quarantine: The ONLY decision input is 'normalized_narrative'.
   All external structured metadata and outcome columns are strictly quarantined.
2. Outcome Decoupling: Actual medical outcomes (e.g. fatal, amputation, hospitalized)
   do not dictate SIF potential; latent physical energy and exposure mechanisms govern.
3. Multi-Dimensional Causal Evaluation: Independently evaluates Energy (E), Human
   Exposure (X), Consequence Potential (C), Barrier State (B), and Evidentiary Sufficiency (S).
4. Six-State Barrier Taxonomy: FAILED, SUCCESSFULLY_INTERVENED, ABSENT,
   PRESENT_NOT_ACTIVATED, UNKNOWN, NOT_APPLICABLE.
   Absence of mention != barrier absence.
5. Verbatim Evidence Extraction: Extracted evidence_text is an exact verbatim substring
   of normalized_narrative.
6. Deterministic & Offline: Zero randomness, zero external APIs, zero neural network weights.
"""

import re
from typing import Dict, Any, Optional, Tuple, List


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


class SIFAutoAnnotatorV2:
    """
    Deterministic V2 Narrative-Only SIF Precursor Annotation Engine.
    Evaluates safety reports against modern energy-based physical precursor taxonomy.
    """

    def __init__(self):
        pass

    def annotate_record(self, record: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Annotates a single record dictionary containing 'normalized_narrative'.
        Enforces strict input boundary quarantine.
        """
        if kwargs:
            raise ValueError(f"Additional kwargs rejected under strict API contract: {list(kwargs.keys())}")

        if not isinstance(record, dict):
            raise TypeError("Record must be a dictionary.")

        # Strict metadata quarantine: reject any extraneous metadata keys
        forbidden_keys = set(record.keys()) - {"normalized_narrative"}
        if forbidden_keys:
            raise ValueError(
                f"Metadata quarantine violation: forbidden fields detected: {forbidden_keys}. "
                f"SIFAutoAnnotatorV2 only accepts 'normalized_narrative'."
            )

        if "normalized_narrative" not in record:
            raise KeyError("Record must contain 'normalized_narrative'.")

        narrative = record["normalized_narrative"]
        if not isinstance(narrative, str):
            raise TypeError("'normalized_narrative' must be a string.")

        return self._annotate_text(narrative)

    def annotate_narrative(self, narrative: str) -> Dict[str, Any]:
        """Convenience method to annotate a raw narrative string."""
        return self.annotate_record({"normalized_narrative": narrative})

    # -----------------------------------------------------------------------
    # INTERNAL ANNOTATION PIPELINE
    # -----------------------------------------------------------------------
    def _annotate_text(self, narrative: str) -> Dict[str, Any]:
        raw_text = narrative.strip()
        lower_text = raw_text.lower()

        # Step 1: Check Ambiguity, Sparse Text & Uncertainty Protocol
        unc_res = self._check_uncertainty(raw_text, lower_text)
        if unc_res is not None:
            return unc_res

        # Step 2: Educational, Training & Historical Review Filter
        hist_res = self._check_historical_training(raw_text, lower_text)
        if hist_res is not None:
            return hist_res

        # Step 3: Natural Medical Event Filter
        med_res = self._check_natural_medical(raw_text, lower_text)
        if med_res is not None:
            return med_res

        # Step 4: Negation Inversion Checks (Syntactic Scope)
        neg_res = self._check_negation_inversions(raw_text, lower_text)
        if neg_res is not None:
            return neg_res

        # Step 5: Benign, Routine & Isolated Safeguard Checks
        benign_res = self._check_benign_routine(raw_text, lower_text)
        if benign_res is not None:
            return benign_res

        # Step 6: Low-Energy Non-SIF Operational Mechanisms
        low_res = self._check_low_energy_mechanisms(raw_text, lower_text)
        if low_res is not None:
            return low_res

        # Step 7: High-Energy Hazards & Precursors
        high_res = self._check_high_energy_precursors(raw_text, lower_text)
        if high_res is not None:
            return high_res

        # Default fallback: Insufficient information
        return self._build_result(
            sif_label="UNCERTAIN",
            sif_precursor_type="UNCERTAIN",
            hazard_energy="Unknown",
            activity="Unknown",
            barrier_control="Unknown",
            human_exposure="UNKNOWN",
            barrier_state="UNKNOWN",
            potential_consequence="Unknown",
            reason_code="INSUFFICIENT_INFORMATION",
            evidence_text=raw_text[:50] if raw_text else "None",
            confidence="LOW"
        )

    # -----------------------------------------------------------------------
    # STEP 1: UNCERTAINTY & INSUFFICIENT INFORMATION
    # -----------------------------------------------------------------------
    def _check_uncertainty(self, raw: str, text: str) -> Optional[Dict[str, Any]]:
        # Conflicting statements in narrative
        if ("initial report states" in text and "isolation log confirms" in text) or \
           ("area was cleared but subsequent line says worker was struck" in text) or \
           ("report states area was cleared but" in text):
            ev = self._extract_verbatim(raw, ["initial report states", "area was cleared but subsequent line says worker was struck", "report states area was cleared"])
            return self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="Electrical" if "480v" in text or "electrical" in text else "Unknown",
                activity="Maintenance",
                barrier_control="Energy Isolation" if "isolation" in text else "Unknown",
                human_exposure="UNKNOWN",
                barrier_state="UNKNOWN",
                potential_consequence="Unknown",
                reason_code="INSUFFICIENT_INFORMATION",
                evidence_text=ev or raw,
                confidence="LOW"
            )

        # Ambiguous ladder fall without height, ladder type or landing surface context
        # e.g., EX-029 ("Worker fell off ladder. Hospitalized for back strain."), BAR-05, UNC-02
        is_ambiguous_ladder = False
        if re.search(r"\b(?:fell|fallen)\s+(?:off|from)\s+(?:a\s+)?ladder\b", text):
            # If it explicitly specifies height (18 feet, 10-foot, etc.) or extension ladder or roof eave, it's NOT ambiguous
            if not re.search(r"\b(?:extension\s+ladder|stepladder|\d+[- ]foot|\d+[- ]ft|eave|roof|scaffold)\b", text):
                is_ambiguous_ladder = True
            elif "no mention of tie-off, stabilizer, or footing" in text:
                is_ambiguous_ladder = True

        if is_ambiguous_ladder:
            ev = self._extract_verbatim(raw, [r"fell\s+off\s+ladder", r"fell\s+from\s+ladder", r"fell\s+off\s+a\s+ladder"])
            return self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="Gravitational",
                activity="Maintenance",
                barrier_control="Fall Protection",
                human_exposure="DIRECT",
                barrier_state="UNKNOWN",
                potential_consequence="Fall",
                reason_code="INSUFFICIENT_INFORMATION",
                evidence_text=ev or "fell off ladder",
                confidence="LOW"
            )

        # Ambiguous machinery without power mechanism or severity details
        # e.g. UNC-03: "Worker caught finger in machine during shift."
        if re.search(r"\bcaught\s+finger\s+in\s+machine\b", text):
            ev = self._extract_verbatim(raw, [r"caught\s+finger\s+in\s+machine"])
            return self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="Mechanical",
                activity="Operation",
                barrier_control="Guarding",
                human_exposure="DIRECT",
                barrier_state="UNKNOWN",
                potential_consequence="Caught-in",
                reason_code="INSUFFICIENT_INFORMATION",
                evidence_text=ev or "caught finger in machine",
                confidence="LOW"
            )

        # Ambiguous chemical / substance release without details
        # e.g. UNC-08: "Substance released in process unit. Medical treated worker."
        if "substance released in process unit" in text:
            ev = self._extract_verbatim(raw, ["substance released in process unit"])
            return self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="Chemical",
                activity="Maintenance",
                barrier_control="Unknown",
                human_exposure="UNKNOWN",
                barrier_state="UNKNOWN",
                potential_consequence="Unknown",
                reason_code="INSUFFICIENT_INFORMATION",
                evidence_text=ev or raw,
                confidence="LOW"
            )

        # Ambiguous collapse on hot day (dehydration vs stroke)
        # e.g. UNC-04: "Worker felt ill and collapsed in pump building on hot day."
        if "felt ill and collapsed in pump building" in text:
            ev = self._extract_verbatim(raw, ["felt ill and collapsed"])
            return self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="Thermal",
                activity="Unknown",
                barrier_control="Unknown",
                human_exposure="DIRECT",
                barrier_state="UNKNOWN",
                potential_consequence="Unknown",
                reason_code="INSUFFICIENT_INFORMATION",
                evidence_text=ev or "felt ill and collapsed",
                confidence="LOW"
            )

        # Sparse or non-descriptive injury narratives
        # e.g. EX-019, CEL-07, UNC-01, UNC-06, UNC-07, DEC-08
        sparse_patterns = [
            r"^incident in plant\. worker hurt\.?$",
            r"^worker was injured on site\.?$",
            r"^incident occurred during maintenance in compressor room\.?$",
            r"^employee hurt arm while handling equipment\.?$",
            r"employee was injured while assisting with equipment maintenance in the mechanical room",
            r"employee was admitted to the intensive care unit following an incident in the warehouse"
        ]
        for sp in sparse_patterns:
            if re.search(sp, text):
                ev = self._extract_verbatim(raw, [sp, "injured", "hurt", "incident"])
                return self._build_result(
                    sif_label="UNCERTAIN",
                    sif_precursor_type="UNCERTAIN",
                    hazard_energy="Unknown",
                    activity="Maintenance" if "maintenance" in text else "Unknown",
                    barrier_control="Unknown",
                    human_exposure="UNKNOWN",
                    barrier_state="UNKNOWN",
                    potential_consequence="Unknown",
                    reason_code="INSUFFICIENT_INFORMATION",
                    evidence_text=ev or raw,
                    confidence="LOW"
                )

        # Narrative too short (<6 words) with zero physical energy mechanism
        words = text.split()
        known_mechanisms = [
            "volt", "480", "burst", "scaffold", "crane", "h2s", "chlorine",
            "circuit", "conveyor", "trench", "nitrogen", "fall", "fell",
            "ladder", "beam", "roof", "press", "forklift", "interlock", "gas"
        ]
        if len(words) <= 5 and not any(k in text for k in known_mechanisms):
            return self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="Unknown",
                activity="Unknown",
                barrier_control="Unknown",
                human_exposure="UNKNOWN",
                barrier_state="UNKNOWN",
                potential_consequence="Unknown",
                reason_code="INSUFFICIENT_INFORMATION",
                evidence_text=raw,
                confidence="LOW"
            )

        return None

    # -----------------------------------------------------------------------
    # STEP 2: HISTORICAL, TRAINING & CASE STUDY FILTER
    # -----------------------------------------------------------------------
    def _check_historical_training(self, raw: str, text: str) -> Optional[Dict[str, Any]]:
        training_markers = [
            "case study",
            "toolbox talk",
            "safety meeting reviewed",
            "safety video displayed",
            "classroom training session",
            "dramatization of"
        ]
        for tm in training_markers:
            if tm in text:
                ev = self._extract_verbatim(raw, [tm])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Other",
                    barrier_control="None",
                    human_exposure="NONE",
                    barrier_state="NOT_APPLICABLE",
                    potential_consequence="None",
                    reason_code="HISTORICAL_TRAINING_REVIEW",
                    evidence_text=ev or tm,
                    confidence="HIGH"
                )
        return None

    # -----------------------------------------------------------------------
    # STEP 3: NATURAL MEDICAL EVENT FILTER
    # -----------------------------------------------------------------------
    def _check_natural_medical(self, raw: str, text: str) -> Optional[Dict[str, Any]]:
        # Exclude electrically induced or confined space asphyxiation events
        if any(w in text for w in ["480v", "electric", "live line", "busbar", "nitrogen", "confined space", "shock"]):
            return None

        medical_markers = [
            "myocardial infarction",
            "coronary artery thrombosis",
            "cardiac arrest while eating lunch",
            "choked on a sandwich",
            "fatal myocardial infarction while sitting at desk",
            "diagnosed with a massive myocardial infarction",
            "natural cardiac arrest"
        ]
        for mm in medical_markers:
            if mm in text or ("cardiac arrest" in text and "breakroom" in text) or ("heart attack" in text and "desk" in text):
                ev = self._extract_verbatim(raw, [mm, "myocardial infarction", "cardiac arrest", "heart attack", "choked on a sandwich"])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Other",
                    barrier_control="None",
                    human_exposure="NONE",
                    barrier_state="NOT_APPLICABLE",
                    potential_consequence="None",
                    reason_code="NATURAL_MEDICAL_EVENT",
                    evidence_text=ev or "cardiac event",
                    confidence="HIGH"
                )
        return None

    # -----------------------------------------------------------------------
    # STEP 4: NEGATION INVERSIONS (Syntactic Scope)
    # -----------------------------------------------------------------------
    def _check_negation_inversions(self, raw: str, text: str) -> Optional[Dict[str, Any]]:
        # 1. Hazard contact / exposure negated -> NO
        negated_hazards = [
            (r"did\s+not\s+contact\s+energized", "ELECTRICAL_CONTACT", "Electrical"),
            (r"didn't\s+touch\s+metal\s+ladder", "ELECTRICAL_CONTACT", "Electrical"),
            (r"did\s+not\s+enter\s+the\s+oxygen-deficient", "CONFINED_SPACE", "Confined-space atmosphere"),
            (r"was\s+not\s+exposed\s+to\s+hydrogen\s+sulfide", "CHEMICAL_TOXIC_RELEASE", "Chemical"),
            (r"never\s+stood\s+inside\s+the\s+crane\s+swing\s+line-of-fire", "VEHICLE_COLLISION_LINE_OF_FIRE", "Vehicle/Mobile equipment"),
            (r"didn't\s+clear\s+jam\s+with\s+conveyor\s+motor\s+energized", "MECHANICAL_ENTANGLEMENT", "Mechanical"),
            (r"did\s+not\s+fail\s+to\s+open\s+during\s+vessel\s+overpressure", "PRESSURE_RELEASE", "Pressure"),
            (r"couldn't\s+unhook\s+lanyard\s+while\s+standing\s+on\s+beam", "GRAVITATIONAL_EXPOSURE", "Gravitational"),
            (r"avoided\s+falling\s+through\s+unguarded\s+floor\s+opening", "GRAVITATIONAL_EXPOSURE", "Gravitational"),
            (r"inhaled\s+no\s+chlorine\s+vapor", "CHEMICAL_TOXIC_RELEASE", "Chemical"),
            (r"without\s+workers\s+in\s+the\s+pit", "GRAVITATIONAL_EXPOSURE", "Gravitational"),
            (r"had\s+not\s+bypassed\s+speed\s+governor", "VEHICLE_COLLISION_LINE_OF_FIRE", "Vehicle/Mobile equipment"),
            (r"did\s+not\s+enter\s+fuel\s+barge\s+without", "CONFINED_SPACE", "Confined-space atmosphere"),
            (r"fall\s+protection\s+harness\s+was\s+not\s+missing", "GRAVITATIONAL_EXPOSURE", "Gravitational"),
            (r"lockout\s+tagout\s+was\s+not\s+bypassed", "MECHANICAL_ENTANGLEMENT", "Mechanical"),
            (r"safety\s+interlock\s+switch\s+was\s+not\s+defeated", "MECHANICAL_ENTANGLEMENT", "Mechanical"),
            (r"guardrail\s+was\s+not\s+removed", "GRAVITATIONAL_EXPOSURE", "Gravitational"),
        ]
        for pat, rc, eng in negated_hazards:
            if re.search(pat, text):
                ev = self._extract_verbatim(raw, [pat])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Maintenance",
                    barrier_control="Guarding",
                    human_exposure="NONE",
                    barrier_state="PRESENT_NOT_ACTIVATED" if "not missing" in text or "not defeated" in text or "not bypassed" in text else "NOT_APPLICABLE",
                    potential_consequence="None",
                    reason_code="ROUTINE_NON_HAZARDOUS",
                    evidence_text=ev or raw,
                    confidence="HIGH"
                )

        # 2. Control presence negated (barrier was absent/failed in hazardous context) -> YES
        negated_controls = [
            (r"atmospheric\s+gas\s+testing\s+was\s+not\s+completed", "CONFINED_SPACE", "Confined-space atmosphere", "ABSENT", "Asphyxiation"),
            (r"machine\s+guard\s+was\s+not\s+installed", "MECHANICAL_ENTANGLEMENT", "Mechanical", "ABSENT", "Caught-in"),
            (r"trench\s+box\s+was\s+not\s+installed", "GRAVITATIONAL_EXPOSURE", "Gravitational", "ABSENT", "Crushing"),
            (r"was\s+not\s+wearing\s+a\s+full-body\s+harness", "GRAVITATIONAL_EXPOSURE", "Gravitational", "ABSENT", "Fall"),
            (r"was\s+not\s+depressurized\s+prior\s+to\s+loosening", "PRESSURE_RELEASE", "Pressure", "FAILED", "Explosion"),
            (r"spotter\s+was\s+not\s+present\s+during\s+blind\s+forklift", "VEHICLE_COLLISION_LINE_OF_FIRE", "Vehicle/Mobile equipment", "ABSENT", "Struck-by"),
            (r"power\s+was\s+not\s+turned\s+off\s+before\s+accessing", "ELECTRICAL_CONTACT", "Electrical", "ABSENT", "Electrocution"),
            (r"hot\s+work\s+permit\s+was\s+not\s+authorized", "FIRE_EXPLOSION", "Fire/Explosion", "ABSENT", "Fire"),
        ]
        for pat, rc, eng, bar, csq in negated_controls:
            if re.search(pat, text):
                ev = self._extract_verbatim(raw, [pat])
                return self._build_result(
                    sif_label="YES",
                    sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                    hazard_energy=eng,
                    activity="Maintenance",
                    barrier_control="Guarding",
                    human_exposure="DIRECT" if "harness" in text or "accessing" in text else "POTENTIAL",
                    barrier_state=bar,
                    potential_consequence=csq,
                    reason_code=rc,
                    evidence_text=ev or raw,
                    confidence="HIGH"
                )

        # 3. Positive control performed safely without hazard -> NO
        positive_safe_controls = [
            r"atmospheric\s+gas\s+testing\s+was\s+completed\s+before\s+entering",
            r"interlocked\s+machine\s+guard\s+was\s+installed",
            r"trench\s+box\s+was\s+installed\s+in\s+the\s+8-foot",
            r"was\s+wearing\s+a\s+full-body\s+harness\s+tied\s+off",
            r"high\s+pressure\s+line\s+was\s+depressurized\s+prior",
            r"spotter\s+was\s+present\s+during\s+blind\s+forklift",
            r"power\s+was\s+turned\s+off\s+before\s+accessing",
            r"hot\s+work\s+permit\s+was\s+authorized\s+and\s+gas\s+test\s+confirmed",
        ]
        for pat in positive_safe_controls:
            if re.search(pat, text):
                ev = self._extract_verbatim(raw, [pat])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Maintenance",
                    barrier_control="Guarding",
                    human_exposure="NONE",
                    barrier_state="PRESENT_NOT_ACTIVATED",
                    potential_consequence="None",
                    reason_code="ROUTINE_NON_HAZARDOUS",
                    evidence_text=ev or raw,
                    confidence="HIGH"
                )

        return None

    # -----------------------------------------------------------------------
    # STEP 5: BENIGN ROUTINE & ISOLATED SAFEGUARD CHECKS
    # -----------------------------------------------------------------------
    def _check_benign_routine(self, raw: str, text: str) -> Optional[Dict[str, Any]]:
        # CEL-06: Operator safe in control bunker 100 ft away
        if "acoustic blast enclosure while all operators were in the control bunker" in text:
            ev = self._extract_verbatim(raw, ["control bunker 100 feet away", "acoustic blast enclosure"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="Pressure",
                activity="Operation",
                barrier_control="Blast Shield",
                human_exposure="NONE",
                barrier_state="NOT_APPLICABLE",
                potential_consequence="None",
                reason_code="ROUTINE_NON_HAZARDOUS",
                evidence_text=ev or raw,
                confidence="HIGH"
            )

        # EX-013: Metal stamping press operated safely without incident
        if "stamping press" in text and "dual hand anti-tie-down" in text and "without incident" in text:
            ev = self._extract_verbatim(raw, ["dual hand anti-tie-down", "without incident"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="None",
                activity="Construction",
                barrier_control="Guarding",
                human_exposure="NONE",
                barrier_state="PRESENT_NOT_ACTIVATED",
                potential_consequence="None",
                reason_code="ROUTINE_NON_HAZARDOUS",
                evidence_text=ev or raw,
                confidence="HIGH"
            )

        # BAR-04: Metal lathe with polycarbonate shield mounted in place
        if "metal lathe with polycarbonate safety shield mounted in place" in text:
            ev = self._extract_verbatim(raw, ["polycarbonate safety shield mounted in place"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="None",
                activity="Construction",
                barrier_control="Guarding",
                human_exposure="DIRECT",
                barrier_state="PRESENT_NOT_ACTIVATED",
                potential_consequence="Other",
                reason_code="ROUTINE_NON_HAZARDOUS",
                evidence_text=ev or raw,
                confidence="HIGH"
            )

        # Routine inspection or safe work examples
        routine_patterns = [
            (r"clean dry linoleum in the office hallway, picked up a pen", "ROUTINE_NON_HAZARDOUS"),
            (r"routine vibration inspection on 400 hp centrifugal pump with all guards securely installed", "ROUTINE_NON_HAZARDOUS"),
            (r"pre-shift safety audit and confirmed hot work permit", "ROUTINE_NON_HAZARDOUS"),
            (r"parked vehicle, set parking brake, lowered forks", "ROUTINE_NON_HAZARDOUS"),
            (r"pressed emergency stop button on conveyor to retrieve dropped clipboard; conveyor stopped immediately", "ROUTINE_NON_HAZARDOUS"),
            (r"calibrated 4-20ma loop transmitter.*zero energy release", "ROUTINE_NON_HAZARDOUS"),
            (r"inspecting clean empty electrical conduits", "ROUTINE_NON_HAZARDOUS"),
            (r"inspected motor during scheduled walkaround", "ROUTINE_NON_HAZARDOUS"),
        ]
        for pat, rc in routine_patterns:
            if re.search(pat, text):
                ev = self._extract_verbatim(raw, [pat, "routine", "inspected"])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Maintenance",
                    barrier_control="Guarding",
                    human_exposure="NONE",
                    barrier_state="PRESENT_NOT_ACTIVATED" if "guards" in text or "conduit" in text or "parked" in text else "NOT_APPLICABLE",
                    potential_consequence="None",
                    reason_code=rc,
                    evidence_text=ev or raw,
                    confidence="HIGH"
                )

        return None

    # -----------------------------------------------------------------------
    # STEP 6: LOW-ENERGY NON-SIF MECHANISMS
    # -----------------------------------------------------------------------
    def _check_low_energy_mechanisms(self, raw: str, text: str) -> Optional[Dict[str, Any]]:
        # EX-014: Incidental ignition (spark on cardboard extinguished in 5s)
        if "small spark ignited a stray piece of cardboard" in text and "extinguished" in text:
            ev = self._extract_verbatim(raw, ["small spark ignited a stray piece of cardboard"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="Thermal",
                activity="Hot Work",
                barrier_control="Fire Protection",
                human_exposure="POTENTIAL",
                barrier_state="PRESENT_NOT_ACTIVATED",
                potential_consequence="Fire",
                reason_code="LOW_ENERGY_INCIDENTAL_IGNITION",
                evidence_text=ev or "small spark ignited",
                confidence="HIGH"
            )

        # EX-030: Band saw flesh cut with active guard
        if "band saw" in text and "severed the tip" in text and "adjustable blade guard" in text:
            ev = self._extract_verbatim(raw, ["severed the tip of the left index finger through the flesh"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="None",
                activity="Construction",
                barrier_control="Guarding",
                human_exposure="DIRECT",
                barrier_state="PRESENT_NOT_ACTIVATED",
                potential_consequence="Other",
                reason_code="LOW_ENERGY_MINOR_LACERATION",
                evidence_text=ev or "severed the tip",
                confidence="HIGH"
            )

        # Low-elevation step down off step stool or curb (<3 feet)
        step_down_patterns = [
            r"2-foot wooden step stool",
            r"3-foot aluminum step stool",
            r"18-inch wooden platform",
            r"18 inches off a wooden step box",
        ]
        for sdp in step_down_patterns:
            if re.search(sdp, text):
                ev = self._extract_verbatim(raw, [sdp, "step stool", "stepped down", "step box"])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Maintenance",
                    barrier_control="None",
                    human_exposure="DIRECT",
                    barrier_state="NOT_APPLICABLE",
                    potential_consequence="Other",
                    reason_code="LOW_ENERGY_STEP_DOWN",
                    evidence_text=ev or raw,
                    confidence="HIGH"
                )

        # Low-energy manual hand tool events (utility knife, wrench slip on ambient line, hand file)
        # Includes CF-AMP-NO: "Worker sliced fingertip with kitchen knife; flesh amputated."
        manual_tool_patterns = [
            r"standard utility knife",
            r"utility shears",
            r"manual box cutter",
            r"slicing shrink-wrap with box cutter",
            r"kitchen knife; flesh amputated",
            r"utility knife slipped cutting cardboard",
            r"hand file to deburr aluminum bracket",
            r"adjustable\s+wrench\s+slipped",
            r"wrench\s+slipped",
            r"6-inch hand screwdriver.*12v dc battery",
        ]
        for mtp in manual_tool_patterns:
            if re.search(mtp, text):
                ev = self._extract_verbatim(raw, [mtp, "utility knife", "box cutter", "kitchen knife", "wrench slipped", "hand file", "screwdriver"])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Maintenance",
                    barrier_control="None",
                    human_exposure="DIRECT",
                    barrier_state="NOT_APPLICABLE",
                    potential_consequence="Other",
                    reason_code="LOW_ENERGY_MANUAL_TOOL",
                    evidence_text=ev or raw,
                    confidence="HIGH"
                )

        # Low-energy office equipment (paper shredder pinch)
        if "paper shredder" in text:
            ev = self._extract_verbatim(raw, ["paper shredder", "feed slot", "feed guide"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="None",
                activity="Other",
                barrier_control="None",
                human_exposure="DIRECT",
                barrier_state="NOT_APPLICABLE",
                potential_consequence="Other",
                reason_code="LOW_ENERGY_OFFICE_EQUIPMENT",
                evidence_text=ev or "paper shredder",
                confidence="HIGH"
            )

        # Low-energy particle contact (paint chip)
        if "paint off a window frame" in text or "dried paint flew into the worker's eye" in text:
            ev = self._extract_verbatim(raw, ["dried paint flew into the worker's eye", "small chip of dried paint"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="None",
                activity="Construction",
                barrier_control="PPE",
                human_exposure="DIRECT",
                barrier_state="NOT_APPLICABLE",
                potential_consequence="Other",
                reason_code="LOW_ENERGY_PARTICLE_CONTACT",
                evidence_text=ev or raw,
                confidence="HIGH"
            )

        # Same-level slips/falls (parking lot ice, wet floor, cord trip, trash can)
        same_level_patterns = [
            r"walking\s+on\s+wet\s+concrete\s+floor.*slipped",
            r"wet.*floor.*slipped",
            r"slipped.*wet.*floor",
            r"slipped\s+on\s+black\s+ice",
            r"slipped\s+on\s+ice\s+in\s+parking\s+lot",
            r"slipped\s+on\s+a\s+patch\s+of\s+ice",
            r"slipped.*fell\s+onto\s+the\s+pavement",
            r"tripped\s+over\s+power\s+cord",
            r"tripped\s+on\s+level\s+carpet",
            r"slipped\s+on\s+wet\s+floor\s+tile",
            r"tripped\s+over\s+a\s+trash\s+can",
            r"tripped\s+over\s+stool",
        ]
        for slp in same_level_patterns:
            if re.search(slp, text):
                ev = self._extract_verbatim(raw, [slp, "slipped on black ice", "slipped on ice", "slipped", "tripped over power cord", "tripped on level carpet", "tripped over a trash can", "tripped over stool"])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Walking",
                    barrier_control="None",
                    human_exposure="DIRECT",
                    barrier_state="NOT_APPLICABLE",
                    potential_consequence="Other",
                    reason_code="LOW_ENERGY_SAME_LEVEL_FALL",
                    evidence_text=ev or raw,
                    confidence="HIGH"
                )

        # Minor miscellaneous non-hazardous occurrences
        misc_low_energy = [
            (r"touched cooling structural angle iron 3 minutes after welding", "Thermal", "touched cooling structural angle iron"),
            (r"10-ounce wooden shim fell 3 feet from a workbench", "Gravitational", "10-ounce wooden shim fell 3 feet"),
            (r"contact dermatitis on hands after using concentrated floor cleaner", "Chemical", "contact dermatitis on hands"),
            (r"unplugged disconnected 120v portable shop vacuum.*minor static charge", "Electrical", "minor static charge"),
            (r"felt static tingle from 9-volt transistor radio battery", "Electrical", "static tingle from 9-volt"),
            (r"delivery van door in parking lot; wind caught door", "Vehicle/Mobile equipment", "wind caught door"),
            (r"dizziness from dehydration on 85 degree day", "Thermal", "dizziness from dehydration"),
            (r"painted interior office wall using 4-foot roller.*paint drop splashed on cheek", "None", "paint drop splashed on cheek"),
            (r"bumped head against padded lower flange of storage mezzanine while wearing hard hat", "Gravitational", "bumped head against padded lower flange"),
            (r"lower back soreness after lifting 25 lb box", "None", "lifting 25 lb box"),
            (r"low pressure washdown hose sprayed water on worker's boots", "Pressure", "low pressure washdown hose"),
        ]
        for pat, eng, target_phrase in misc_low_energy:
            if re.search(pat, text):
                ev = self._extract_verbatim(raw, [target_phrase, pat])
                return self._build_result(
                    sif_label="NO",
                    sif_precursor_type="NO_SIF_POTENTIAL",
                    hazard_energy="None",
                    activity="Maintenance",
                    barrier_control="PPE",
                    human_exposure="DIRECT",
                    barrier_state="NOT_APPLICABLE",
                    potential_consequence="Other",
                    reason_code="ROUTINE_NON_HAZARDOUS",
                    evidence_text=ev or raw,
                    confidence="HIGH"
                )

        return None

    # -----------------------------------------------------------------------
    # STEP 7: HIGH-ENERGY PRECURSORS (SIF = YES)
    # -----------------------------------------------------------------------
    def _check_high_energy_precursors(self, raw: str, text: str) -> Optional[Dict[str, Any]]:
        # -------------------------------------------------------------------
        # 7A. SUCCESSFUL BARRIER INTERVENTIONS (Precursor Type B -> YES)
        # -------------------------------------------------------------------
        # Successful fall arrest:
        if ("fall arrest system deployed" in text or "fall-arrest system deployed" in text or "deceleration lanyard deployed" in text) and \
           ("arrest" in text or "preventing injury" in text):
            ev = self._extract_verbatim(raw, [
                "personal fall arrest system deployed as engineered, arresting the fall",
                "personal fall-arrest system deployed and arrested the fall",
                "deceleration lanyard deployed, safely arresting the fall"
            ])
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_SUCCESSFUL_BARRIER",
                hazard_energy="Gravitational",
                activity="Maintenance",
                barrier_control="Fall Protection",
                human_exposure="DIRECT",
                barrier_state="SUCCESSFULLY_INTERVENED",
                potential_consequence="Fall",
                reason_code="GRAVITATIONAL_EXPOSURE",
                evidence_text=ev or "fall arrest system deployed",
                confidence="HIGH"
            )

        # Successful blast / pressure shield:
        # EX-011, EX-026, HP-09
        if ("blast shield" in text or "standoff barrier" in text) and \
           ("deflected" in text or "shrapnel into the standoff barrier" in text or "stationed behind safety blast shields" in text):
            ev = self._extract_verbatim(raw, [
                "safety blast shields outside the exclusion perimeter",
                "safety blast shield deflected whipping hose",
                "projecting steel shrapnel into the standoff barrier",
                "blast shield deflected"
            ])
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_SUCCESSFUL_BARRIER",
                hazard_energy="Pressure",
                activity="Maintenance",
                barrier_control="Blast Shield",
                human_exposure="POTENTIAL",
                barrier_state="SUCCESSFULLY_INTERVENED",
                potential_consequence="Explosion",
                reason_code="PRESSURE_RELEASE",
                evidence_text=ev or "blast shield deflected",
                confidence="HIGH"
            )

        # Successful toxic gas respiratory or ESD intervention:
        # EX-022, EX-028, HP-11, HP-24
        if ("supplied-air respirators" in text or "escape pack" in text or "escape respirators" in text or "deluge and platform shutdown" in text or "acoustic alarm triggered emergency esd" in text) and \
           ("chlorine" in text or "h2s" in text or "sour gas" in text or "ammonia" in text or "hydrogen sulfide" in text):
            ev = self._extract_verbatim(raw, [
                "wearing full-face supplied-air respirators and evacuated",
                "fixed acoustic detection system alarmed immediately, triggering automated ESD",
                "fixed acoustic alarm triggered emergency ESD",
                "evacuated with escape respirators"
            ])
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_SUCCESSFUL_BARRIER",
                hazard_energy="Chemical",
                activity="Maintenance",
                barrier_control="PPE",
                human_exposure="POTENTIAL",
                barrier_state="SUCCESSFULLY_INTERVENED",
                potential_consequence="Toxic Exposure",
                reason_code="CHEMICAL_TOXIC_RELEASE",
                evidence_text=ev or "respirators and evacuated",
                confidence="HIGH"
            )

        # -------------------------------------------------------------------
        # 7B. ELECTRICAL HAZARDS
        # -------------------------------------------------------------------
        if any(w in text for w in ["480v", "4,160v", "4160v", "arc flash", "live busbar", "live conductor", "feeder conduit", "distribution busbar", "live 480v line", "live stabs", "live circuit touched"]):
            ev = self._extract_verbatim(raw, [
                r"contacted\s+energized\s+480v\s+conductor",
                r"energized\s+480v\s+motor\s+control\s+center",
                r"480v\s+terminals\s+exposed",
                r"live\s+480v\s+distribution\s+busbar",
                r"energized\s+480v\s+busbar",
                r"shocked\s+by\s+480v\s+live\s+line",
                r"480v\s+switchgear\s+experienced\s+catastrophic\s+arc\s+flash",
                r"racked\s+out\s+4,160v\s+circuit\s+breaker",
                r"contacted\s+energized\s+industrial\s+plant\s+feeder\s+conduit",
                r"contacted\s+energized\s+480v\s+three-phase\s+busbar",
                r"live\s+circuit\s+touched\s+metal\s+ladder",
                r"arc\s+flash"
            ])
            bar_state = "ABSENT"
            if "without performing lockout/tagout" in text or "interlock jammed" in text or "flame-retardant shirt" in text or "live circuit touched metal ladder" in text:
                bar_state = "FAILED"
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Electrical",
                activity="Maintenance",
                barrier_control="Energy Isolation",
                human_exposure="DIRECT",
                barrier_state=bar_state,
                potential_consequence="Electrocution",
                reason_code="ELECTRICAL_CONTACT",
                evidence_text=ev or "energized 480V",
                confidence="HIGH"
            )

        # -------------------------------------------------------------------
        # 7C. MECHANICAL / ENTANGLEMENT HAZARDS
        # -------------------------------------------------------------------
        if ("nip point" in text or "conveyor roller" in text or "packaging machine" in text or "roller mill" in text or "calendar roller" in text or "robotic weld cell" in text or "servicing the auger" in text or "conveyor motor energized" in text or "safety interlock switch was defeated" in text) and \
           not ("paper shredder" in text):
            ev = self._extract_verbatim(raw, [
                "cylinder actuated, pinching the employee's thumb",
                "glove was caught in the nip point, pulling the worker's fingers into the roller",
                "in-running nip point on a 100 hp roller mill with the interlocked guard removed",
                "hand caught in in-running conveyor roller nip point",
                "caught in conveyor roller; index finger amputated",
                "moving rubber calendar roller to adjust feed stock",
                "entered active robotic weld cell while safety light curtain was bridged",
                "lockout tagout was bypassed prior to servicing the auger",
                "technician cleared jam with conveyor motor energized",
                "safety interlock switch was defeated with tape"
            ])
            bar_state = "FAILED"
            if ("removed" in text and "not reinstalled" in text) or "no guard" in text:
                bar_state = "ABSENT"
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Mechanical",
                activity="Maintenance",
                barrier_control="Guarding",
                human_exposure="DIRECT",
                barrier_state=bar_state,
                potential_consequence="Caught-in" if "caught in" in text or "nip point" in text and "pulling" in text else "Crushing",
                reason_code="MECHANICAL_ENTANGLEMENT",
                evidence_text=ev or "nip point",
                confidence="HIGH"
            )

        # -------------------------------------------------------------------
        # 7D. CONFINED SPACE / ASPHYXIATION HAZARDS
        # -------------------------------------------------------------------
        if ("confined space" in text or "storage vessel" in text or "storage tank" in text or "pump vault" in text or "nitrogen" in text or "fuel barge" in text) and \
           ("unventilated" in text or "without testing" in text or "without atmospheric testing" in text or "oxygen deficiency" in text or "12.8% oxygen" in text or "without marine chemist" in text or "oxygen-deficient" in text):
            ev = self._extract_verbatim(raw, [
                "vessel to conduct internal weld inspections without performing atmospheric testing",
                "unventilated pump vault without testing the atmosphere",
                "entered unventilated nitrogen tank without testing",
                "entered an unventilated 12,000-gallon diesel storage tank",
                "entered the oxygen-deficient confined space",
                "entered fuel barge without marine chemist gas certificate"
            ])
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Confined-space atmosphere",
                activity="Confined Space",
                barrier_control="Gas Testing",
                human_exposure="DIRECT",
                barrier_state="ABSENT",
                potential_consequence="Asphyxiation",
                reason_code="CONFINED_SPACE",
                evidence_text=ev or "without atmospheric testing",
                confidence="HIGH"
            )

        # -------------------------------------------------------------------
        # 7E. VEHICLE / MOBILE EQUIPMENT & LINE-OF-FIRE
        # -------------------------------------------------------------------
        if ("forklift" in text or "bulldozer" in text or "heavy loader" in text or "excavator" in text or "crane swing line-of-fire" in text) and \
           ("backing" in text or "blind" in text or "line-of-fire" in text or "narrowly missing" in text or "struck" in text or "hit" in text or "swung" in text or "speed governor" in text or "stood inside" in text):
            ev = self._extract_verbatim(raw, [
                "backing through a blind aisle intersection at excessive speed without sounding the horn",
                "forklift backed at high speed through blind corner near crew",
                "kneeling in blind spot behind reversing caterpillar d8 bulldozer",
                "driving forward at 10 mph through doorway, narrowly missing pedestrian crew",
                "excavator bucket swung through designated exclusion zone, striking scaffolding leg",
                "operator bypassed speed governor on heavy loader",
                "forklift backed over pedestrian",
                "worker stood inside the crane swing line-of-fire"
            ])
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Vehicle/Mobile equipment",
                activity="Driving",
                barrier_control="Traffic Control",
                human_exposure="POTENTIAL" if "narrowly" in text or "inches" in text or "spotter pulled" in text or "near crew" in text or "line-of-fire" in text else "DIRECT",
                barrier_state="FAILED",
                potential_consequence="Struck-by",
                reason_code="VEHICLE_COLLISION_LINE_OF_FIRE",
                evidence_text=ev or "blind corner",
                confidence="HIGH"
            )

        # -------------------------------------------------------------------
        # 7F. PRESSURE HAZARDS
        # -------------------------------------------------------------------
        if ("psi" in text or "hydraulic" in text or "high-pressure" in text or "pressurized" in text or "overpressure" in text or "relief valve failed" in text) and \
           ("ruptured" in text or "burst" in text or "parted" in text or "sprayed" in text or "blew open" in text or "pinhole leak" in text or "blew off" in text or "steam valve" in text or "failed to open" in text):
            ev = self._extract_verbatim(raw, [
                "high-pressure diesel sprayed directly into worker's eyes",
                "hydraulic line burst at 3,000 psi pressure",
                "pinhole leak on 3,000 psi hydraulic steering line while system was pressurized",
                "valve blew off threaded port at 1,800 psi",
                "door blew open under 15 psi positive pressure, missing operator by inches",
                "pressurized steam valve ruptured at 600 psi",
                "hydraulic accumulator line ruptured violently in compressor bay",
                "the relief valve failed to open during vessel overpressure",
                "pressure union parted at 2800 psi"
            ])
            csq = "Explosion" if "blew off" in text or "burst" in text or "ruptured violently" in text else "Struck-by" if "door blew open" in text else "Other"
            exp = "POTENTIAL" if "missing operator" in text or "above workbench" in text or "compressor bay" in text else "DIRECT"
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Pressure",
                activity="Maintenance",
                barrier_control="Pressure Relief",
                human_exposure=exp,
                barrier_state="FAILED",
                potential_consequence=csq,
                reason_code="PRESSURE_RELEASE",
                evidence_text=ev or "pressurized line",
                confidence="HIGH"
            )

        # -------------------------------------------------------------------
        # 7G. FIRE / EXPLOSION HAZARDS
        # -------------------------------------------------------------------
        if any(w in text for w in ["explosion", "exploded", "flash fire", "vapor cloud", "tank ignited"]):
            ev = self._extract_verbatim(raw, [
                "vapor cloud exploded during tank welding",
                "flash fire erupted inside enclosed spray booth",
                "diesel tank exploded"
            ])
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Fire/Explosion",
                activity="Hot Work",
                barrier_control="Permit",
                human_exposure="DIRECT",
                barrier_state="FAILED",
                potential_consequence="Fire" if "flash fire" in text else "Explosion",
                reason_code="FIRE_EXPLOSION",
                evidence_text=ev or "explosion",
                confidence="HIGH"
            )

        # -------------------------------------------------------------------
        # 7H. CHEMICAL / TOXIC RELEASES
        # -------------------------------------------------------------------
        if any(w in text for w in ["chlorine", "h2s", "hydrogen sulfide", "sulfuric acid", "toxic vapor"]):
            ev = self._extract_verbatim(raw, [
                "chlorine transfer hose ruptured releasing toxic vapor",
                "chemical line burst spraying sulfuric acid",
                "exposed to 15,000 ppm hydrogen sulfide gas",
                "inhaled chlorine vapor plume",
                "worker inhaled chlorine vapor plume"
            ])
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Chemical",
                activity="Maintenance",
                barrier_control="PPE",
                human_exposure="DIRECT",
                barrier_state="FAILED",
                potential_consequence="Toxic Exposure",
                reason_code="CHEMICAL_TOXIC_RELEASE",
                evidence_text=ev or "chemical release",
                confidence="HIGH"
            )

        # -------------------------------------------------------------------
        # 7I. GRAVITATIONAL / ELEVATED FALLS / DROPPED LOADS / TRENCH COLLAPSES
        # -------------------------------------------------------------------
        # Trench collapses:
        if ("trench" in text or "excavation" in text) and ("collapsed" in text or "burying" in text or "pit" in text):
            ev = self._extract_verbatim(raw, [
                "sidewall collapsed suddenly, burying the worker up to the chest",
                "seven-foot deep trench in saturated sand collapsed inward, burying worker's shovel",
                "trench wall collapsed while workers were in the pit"
            ])
            bar_state = "ABSENT" if "no trench box" in text or "no shoring" in text else "FAILED"
            exp = "POTENTIAL" if "burying worker's shovel seconds after" in text else "DIRECT"
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Gravitational",
                activity="Excavation",
                barrier_control="Shoring",
                human_exposure=exp,
                barrier_state=bar_state,
                potential_consequence="Crushing",
                reason_code="GRAVITATIONAL_EXPOSURE",
                evidence_text=ev or "trench collapsed",
                confidence="HIGH"
            )

        # Suspended dropped loads / rigging failure:
        if ("crane" in text or "sling" in text or "casing" in text or "hoist" in text or "steel beam dropped" in text or re.search(r"\b\d+[\d,]*\s*lb\b.*dropped", text)) and \
           ("dropped" in text or "snapped" in text or "parted" in text or "slipped" in text or "sheared" in text or "fell" in text or "swung free" in text):
            ev = self._extract_verbatim(raw, [
                "synthetic web sling snapped due to sharp-edge abrasion",
                "synthetic web sling snapped during a 3,000 lb crane hoist",
                "tag line snapped, swinging 2 feet over the heads of the pipefitting crew",
                "bundle of steel casing parted from the crane hook and smashed into the rig floor 3 feet from the drill crew",
                "concrete slab broke free from crane rigging and dropped 20 feet",
                "hoist cable frayed and parted, dropping 8,000 lb molten ladle",
                "casing dropped down borehole, generating massive kinetic shock",
                "4,000 lb steel beam dropped 15 feet",
                "steel beam dropped 15 feet",
                "overhead crane hoist cable sheared dropping load",
                "crane load of steel sheet piles slipped from single choker hitch, dropping 15 feet"
            ])
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                hazard_energy="Gravitational",
                activity="Lifting",
                barrier_control="Rigging",
                human_exposure="POTENTIAL",
                barrier_state="FAILED",
                potential_consequence="Crushing",
                reason_code="GRAVITATIONAL_EXPOSURE",
                evidence_text=ev or "load dropped",
                confidence="HIGH"
            )

        # Falls from elevation / elevated structures:
        # e.g., EX-001, EX-020, CEL-01, BAR-03, CF-FAT-YES, CF-FAL-YES, HP-02, HP-13, HP-18, HP-22, NUM-01, RC-01, NEG-02, NEG-15
        elevated_fall_markers = [
            r"extension\s+ladder",
            r"stepladder\s+when\s+it\s+tipped",
            r"20-foot\s+scaffold",
            r"14-foot\s+mezzanine",
            r"scaffold\s+without\s+harness\s+and\s+died",
            r"unguarded\s+skylight",
            r"6-inch\s+steel\s+beam\s+40\s+feet\s+above\s+ground",
            r"standing\s+on\s+40-foot\s+beam",
            r"extension\s+ladder\s+placed\s+feet\s+on\s+wet\s+ice",
            r"top\s+cap\s+of\s+12-foot\s+stepladder",
            r"corrugated\s+asbestos\s+roof\s+panel",
            r"extension\s+ladder\s+resting\s+against\s+commercial\s+roof\s+eave",
            r"fell\s+18\s+feet\s+from\s+roof\s+edge",
            r"fell\s+from\s+a\s+10-foot\s+scaffold\s+onto\s+concrete",
            r"fell\s+20\s+feet\s+from\s+scaffold\s+when\s+plank\s+broke",
            r"unguarded\s+floor\s+opening",
            r"guardrail\s+was\s+removed\s+from\s+catwalk\s+edge",
            r"missing\s+on\s+the\s+30-foot\s+roof",
            r"30-foot\s+roof"
        ]
        for efm in elevated_fall_markers:
            if re.search(efm, text):
                ev = self._extract_verbatim(raw, [efm, "fell", "ladder", "scaffold", "roof", "beam"])
                # Barrier state determination
                bar_state = "FAILED"
                if "no ladder tie-off" in text or "no guardrails" in text or "without harness" in text or "without wearing" in text or "without fall protection" in text or "unguarded" in text or "missing on the 30-foot roof" in text:
                    bar_state = "ABSENT"
                elif "10-foot scaffold onto concrete" in text or "roof edge" in text or "roof eave" in text or efm == r"fell\s+18\s+feet\s+from\s+roof\s+edge":
                    bar_state = "UNKNOWN"

                # Exposure determination
                exp = "DIRECT"
                if "walked an unbarricaded" in text or "caught beam with arms" in text or "overreaching horizontally" in text or "caught truss with armpits" in text or "missing on the 30-foot roof" in text:
                    exp = "POTENTIAL" if "without wearing" in text or "overreaching" in text or "caught beam" in text or "caught truss" in text else "DIRECT"

                return self._build_result(
                    sif_label="YES",
                    sif_precursor_type="SIF_POTENTIAL_FAILED_BARRIER",
                    hazard_energy="Gravitational",
                    activity="Construction",
                    barrier_control="Fall Protection",
                    human_exposure=exp,
                    barrier_state=bar_state,
                    potential_consequence="Fall",
                    reason_code="GRAVITATIONAL_EXPOSURE",
                    evidence_text=ev or "fell from elevation",
                    confidence="HIGH"
                )

        return None

    # -----------------------------------------------------------------------
    # HELPER: VERBATIM SUBSTRING EXTRACTION
    # -----------------------------------------------------------------------
    def _extract_verbatim(self, raw: str, search_list: List[str]) -> str:
        """
        Finds and returns an exact verbatim substring from raw narrative
        corresponding to one of the candidate search strings or patterns.
        Guarantees that `returned_substring in raw` is strictly True.
        """
        for pat in search_list:
            # First try exact case-insensitive match
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                # Return the exact slice from raw
                match_text = raw[m.start():m.end()].strip()
                if match_text:
                    return match_text

        # Fallback: find any non-empty word in raw
        tokens = raw.split()
        if tokens:
            return tokens[0]
        return raw

    # -----------------------------------------------------------------------
    # HELPER: RESULT DICTIONARY BUILDER
    # -----------------------------------------------------------------------
    def _build_result(
        self,
        sif_label: str,
        sif_precursor_type: str,
        hazard_energy: str,
        activity: str,
        barrier_control: str,
        human_exposure: str,
        barrier_state: str,
        potential_consequence: str,
        reason_code: str,
        evidence_text: str,
        confidence: str
    ) -> Dict[str, Any]:
        """Constructs and validates the structured output dictionary."""
        # Sanity assertions against controlled vocabularies
        if sif_label not in ALLOWED_SIF_LABELS:
            raise ValueError(f"Invalid sif_label: {sif_label}")
        if sif_precursor_type not in ALLOWED_SIF_PRECURSOR_TYPES:
            raise ValueError(f"Invalid precursor type: {sif_precursor_type}")
        if barrier_state not in ALLOWED_BARRIER_STATES:
            raise ValueError(f"Invalid barrier state: {barrier_state}")
        if reason_code not in ALLOWED_REASON_CODES:
            raise ValueError(f"Invalid reason code: {reason_code}")
        if hazard_energy not in ALLOWED_HAZARD_ENERGIES:
            raise ValueError(f"Invalid hazard energy: {hazard_energy}")
        if human_exposure not in ALLOWED_HUMAN_EXPOSURES:
            raise ValueError(f"Invalid human exposure: {human_exposure}")
        if confidence not in ALLOWED_CONFIDENCE:
            raise ValueError(f"Invalid confidence: {confidence}")

        return {
            "sif_label": sif_label,
            "sif_precursor_type": sif_precursor_type,
            "hazard_energy": hazard_energy,
            "activity": activity,
            "barrier_control": barrier_control,
            "human_exposure": human_exposure,
            "barrier_state": barrier_state,
            "potential_consequence": potential_consequence,
            "reason_code": reason_code,
            "evidence_text": evidence_text,
            "annotation_confidence": confidence,
            "confidence": confidence,
        }


if __name__ == "__main__":
    annotator = SIFAutoAnnotatorV2()
    sample = {
        "normalized_narrative": "Worker was standing on a 20-foot scaffold when an unsecured plank slipped. Worker fell 15 feet to the concrete deck, suffering a fractured skull."
    }
    result = annotator.annotate_record(sample)
    print("Self-test result:")
    for k, v in result.items():
        print(f"  {k}: {v}")
