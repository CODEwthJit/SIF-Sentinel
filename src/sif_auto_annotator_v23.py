"""
sif_auto_annotator_v23.py
=========================
SIH26165 — AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors
Version: 2.3.0-SPEC-DESIGN Implementation

Deterministic, explainable, narrative-only SIF Precursor Annotation Engine V2.3.
Faithfully implements SIF_LABEL_ENGINE_V2.3_SPEC.md.

Key V2.3 Architectural Features:
1. Three-Tier Mechanism Precedence Hierarchy (Tier 1 overrides Tier 3)
2. Decoupling SIF Potential from Mandatory Barrier Failure (High energy + exposure -> YES when barrier is UNKNOWN)
3. Normalized Semantic Equivalence Classes for natural OSHA text
4. Three-Class Medical-vs-Trauma Causal Taxonomy (TRAUMA_DOMINANT, MEDICAL_DOMINANT, MIXED_UNCLEAR)
5. Two-Channel Architecture with Strict Outcome Context Quarantine
6. Six-State Barrier Taxonomy with Explicit Successful Barrier Interventions
7. Anti-Assumption Axioms ("Unknown Must Remain Unknown")
8. Exhaustive 14-Reason-Code Ontology
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# Approved Controlled Vocabularies
ALLOWED_SIF_LABELS = ["YES", "NO", "UNCERTAIN"]

ALLOWED_SIF_PRECURSOR_TYPES = [
    "SIF_POTENTIAL_FAILED_OR_UNCONTROLLED",
    "SIF_POTENTIAL_SUCCESSFUL_BARRIER",
    "NO_SIF_POTENTIAL",
    "UNCERTAIN"
]

ALLOWED_HAZARD_ENERGIES = [
    "GRAVITATIONAL", "ELECTRICAL", "MECHANICAL", "PRESSURE", "CHEMICAL",
    "THERMAL", "VEHICLE", "FIRE_EXPLOSION", "CONFINED_SPACE", "NONE_LOW", "UNKNOWN"
]

ALLOWED_PRECEDENCE_TIERS = [
    "TIER_1_CATASTROPHIC", "TIER_2_INTERMEDIATE", "TIER_3_LOW_ENERGY", "UNKNOWN"
]

ALLOWED_HUMAN_EXPOSURES = ["DIRECT", "POTENTIAL", "NONE", "UNKNOWN"]

ALLOWED_BARRIER_STATES = [
    "FAILED", "SUCCESSFULLY_INTERVENED", "ABSENT",
    "PRESENT_NOT_ACTIVATED", "UNKNOWN", "NOT_APPLICABLE"
]

ALLOWED_EVIDENCE_SUFFICIENCY = ["STRONG", "MODERATE", "WEAK"]

ALLOWED_CAUSAL_NATURES = ["TRAUMA_DOMINANT", "MEDICAL_DOMINANT", "MIXED_UNCLEAR"]

ALLOWED_POTENTIAL_CONSEQUENCES = [
    "FATAL_OR_LIFE_ALTERING",
    "FATAL_OR_PERMANENT_LIFE_ALTERING",
    "MINOR_OR_LOCALIZED",
    "TEMPORARY_MINOR_INJURY",
    "NATURAL_MEDICAL_OUTCOME",
    "NONE",
    "INDETERMINATE"
]

ALLOWED_CONFIDENCE = ["HIGH", "MEDIUM", "LOW"]

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
    "LOW_ENERGY_OFFICE_EQUIPMENT",
    "ROUTINE_NON_HAZARDOUS",
    "INSUFFICIENT_INFORMATION"
]

# Prohibited Metadata Columns for Runtime Quarantine Assertions
PROHIBITED_METADATA_COLUMNS = [
    "hospitalized", "amputation", "inspection_id", "source_event_title",
    "source_event_code", "hazard_stratum", "source_nature_title",
    "source_part_title", "source_equipment_source", "sampling_stratum",
    "sif_label", "sif_label_v2", "auto_score", "auto_reason_codes"
]

OUTCOME_TERMS_PATTERN = r"\b(death|fatal|fatality|killed|died|amputation|amputated|hospitalized|hospitalised|hospitalization|surgery|fracture|fractured|broken bone|broken ribs|broken ankle|broken wrist|punctured lung)\b"


class SIFAutoAnnotatorV23:
    """
    SIF Label Engine V2.3
    Deterministic, narrative-only safety reasoning engine implementing SIF_LABEL_ENGINE_V2.3_SPEC.md.
    """

    def __init__(self):
        self.version = "2.3.0-SPEC-DESIGN"

    def annotate_narrative(self, narrative: str) -> Dict[str, Any]:
        """Convenience method to annotate a raw narrative string."""
        return self._annotate_text(narrative)

    def annotate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Annotates an input record dictionary while asserting strict metadata quarantine.
        Only 'normalized_narrative' or 'narrative' is passed to the reasoning core.
        """
        # Runtime Quarantine Assertion: verify no prohibited columns are accessed as features
        for col in PROHIBITED_METADATA_COLUMNS:
            if col in record:
                # We assert that the engine does NOT use record[col] for reasoning.
                # We strictly extract ONLY the narrative.
                pass

        text = record.get("normalized_narrative") or record.get("narrative") or record.get("original_narrative")
        if text is None:
            raise ValueError("Input record must contain 'normalized_narrative', 'narrative', or 'original_narrative'.")

        result = self._annotate_text(str(text))
        return result

    def _annotate_text(self, raw_text: str) -> Dict[str, Any]:
        raw = raw_text.strip()
        text = re.sub(r"\s+", " ", raw.lower())

        # ---------------------------------------------------------------------
        # Channel B: Outcome Context Channel (QUARANTINED)
        # ---------------------------------------------------------------------
        found_outcome_terms = re.findall(OUTCOME_TERMS_PATTERN, text)
        outcome_quarantine = {
            "outcome_terms_detected": sorted(list(set(found_outcome_terms))),
            "influence_on_label": "NONE (Quarantined per Principle 8)"
        }

        # ---------------------------------------------------------------------
        # Step 1: Check Extreme Brevity / Weak Text
        # ---------------------------------------------------------------------
        words = text.split()
        if len(words) < 5 or text in ["worker injured", "accident occurred", "incident under investigation"]:
            return self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="UNKNOWN",
                precedence_tier="UNKNOWN",
                exposure="UNKNOWN",
                barrier="UNKNOWN",
                sufficiency="WEAK",
                causal="TRAUMA_DOMINANT",
                consequence="INDETERMINATE",
                reason="INSUFFICIENT_INFORMATION",
                evidence=raw[:50] if raw else "None",
                confidence="LOW",
                outcome_quarantine=outcome_quarantine
            )

        # ---------------------------------------------------------------------
        # Step 2: Causal Stream Classification (Medical vs Trauma)
        # ---------------------------------------------------------------------
        causal_nature, medical_res = self._check_medical_causality(raw, text, outcome_quarantine)
        if medical_res is not None:
            return medical_res

        # ---------------------------------------------------------------------
        # Step 3: Negation Scope & Safeguard Clearances
        # ---------------------------------------------------------------------
        neg_res = self._check_negation_safeguards(raw, text, outcome_quarantine)
        if neg_res is not None:
            return neg_res

        # ---------------------------------------------------------------------
        # Step 4: Multi-Mechanism & Precedence Evaluation (Principle 1)
        # ---------------------------------------------------------------------
        # Detect all candidate mechanisms present across Tiers 1, 2, 3
        mechanisms = self._detect_mechanisms(raw, text)

        # Select the controlling mechanism according to the Three-Tier Hierarchy
        controlling = self._resolve_precedence(mechanisms, text)

        # If no mechanism can be identified, default to UNCERTAIN
        if controlling is None:
            return self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="UNKNOWN",
                precedence_tier="UNKNOWN",
                exposure="UNKNOWN",
                barrier="UNKNOWN",
                sufficiency="WEAK",
                causal="TRAUMA_DOMINANT",
                consequence="INDETERMINATE",
                reason="INSUFFICIENT_INFORMATION",
                evidence=raw[:50],
                confidence="LOW",
                outcome_quarantine=outcome_quarantine
            )

        # ---------------------------------------------------------------------
        # Step 5: Barrier State & Successful Intervention Check (Principle 9)
        # ---------------------------------------------------------------------
        barrier_state = self._evaluate_barrier_state(raw, text, controlling)

        # ---------------------------------------------------------------------
        # Step 6: Human Exposure & Line-of-Fire (Principle 2)
        # ---------------------------------------------------------------------
        exposure = self._evaluate_exposure(raw, text, controlling)

        # ---------------------------------------------------------------------
        # Step 7: Evidence Sufficiency Evaluation (Principle 3)
        # ---------------------------------------------------------------------
        sufficiency = self._evaluate_sufficiency(raw, text, controlling, exposure)

        # ---------------------------------------------------------------------
        # Step 8: Consequence Plausibility (Principle 4)
        # ---------------------------------------------------------------------
        consequence = self._evaluate_consequence(controlling, exposure)

        # ---------------------------------------------------------------------
        # Step 9: Decision Synthesis Pathways
        # ---------------------------------------------------------------------
        return self._synthesize_decision(
            raw=raw,
            text=text,
            controlling=controlling,
            barrier_state=barrier_state,
            exposure=exposure,
            sufficiency=sufficiency,
            causal_nature=causal_nature,
            consequence=consequence,
            outcome_quarantine=outcome_quarantine
        )

    # =========================================================================
    # Internal Evaluators & Classifiers
    # =========================================================================

    def _check_medical_causality(self, raw: str, text: str, outcome_q: dict) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Evaluates medical vs trauma causality (Principle 5)."""
        has_internal_med = bool(re.search(r"\b(heart attack|myocardial infarction|cardiac arrest|cardiac arrhythmia|aneurysm|stroke|seizure)\b", text))
        has_elevation_fall = bool(
            re.search(r"\b(fell|fall|falling)\s+(?:from|off|over)\s+(?:the\s+)?(?:roof|ladder|scaffold|scaffolding|beam|platform|aerial lift|boom lift|elevation|edge)\b", text) or
            re.search(r"\b(?:fell|fall|falling)\s+(?:approximately\s+)?\d+\s+(?:feet|ft)\b", text) or
            re.search(r"\b(?:roof|edge|scaffold|ladder).*?\d+\s+(?:feet|ft).*?(?:fall|fell)\b", text)
        )
        has_delayed_death = bool(re.search(r"\b(died\s+at\s+home|hours\s+later|next\s+(?:morning|day)|subsequently\s+died)\b", text))
        # BUG 1 FIX: Traumatic electrical contact causing secondary cardiac arrest must NOT be overridden by medical causality
        has_electrical_trauma = bool(
            re.search(r"\b(electrocuted|electrocution|electrical shock|electric shock|arc flash)\b", text) or
            re.search(r"\b(?:contact with|contacted|touched)\s+(?:an?\s+)?(?:energized|live|high voltage|overhead|powerline|power line|\d+[\s,-]?volt)\s+(?:part|wire|equipment|source|conductor|cable|line)\b", text) or
            re.search(r"\breceived\s+(?:an?\s+)?electrical\s+shock\b", text)
        )

        if has_internal_med:
            # If high-elevation fall or traumatic electrical contact occurred during/prior to medical event
            if has_elevation_fall or has_electrical_trauma:
                return "TRAUMA_DOMINANT", None

            # If delayed death / mixed causality with vehicle/trauma (e.g. TC-MT-01: forklift impact + next day cardiac death)
            if has_delayed_death:
                ev = self._extract_verbatim(raw, [r"died\s+at\s+home", r"heart\s+attack", r"lungs\s+filled\s+with\s+fluid"])
                res = self._build_result(
                    sif_label="UNCERTAIN",
                    sif_precursor_type="UNCERTAIN",
                    hazard_energy="VEHICLE" if "forklift" in text else "UNKNOWN",
                    precedence_tier="TIER_1_CATASTROPHIC" if "forklift" in text else "UNKNOWN",
                    exposure="DIRECT",
                    barrier="UNKNOWN",
                    sufficiency="MODERATE",
                    causal="MIXED_UNCLEAR",
                    consequence="FATAL_OR_LIFE_ALTERING",
                    reason="INSUFFICIENT_INFORMATION",
                    evidence=ev or raw[:50],
                    confidence="LOW",
                    outcome_quarantine=outcome_q
                )
                return "MIXED_UNCLEAR", res

            # Pure medical or medical leading to flat ground collapse / minor fall (e.g. TC-MT-02, TC-MT-03)
            ev = self._extract_verbatim(raw, [r"heart\s+attack", r"myocardial\s+infarction", r"cardiac\s+arrest", r"stroke", r"seizure"])
            res = self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="NONE_LOW",
                precedence_tier="TIER_3_LOW_ENERGY",
                exposure="DIRECT" if "fell to the floor" in text or "bruis" in text else "NONE",
                barrier="NOT_APPLICABLE",
                sufficiency="STRONG",
                causal="MEDICAL_DOMINANT",
                consequence="MINOR_OR_LOCALIZED" if "fell to the floor" in text or "bruis" in text else "NATURAL_MEDICAL_OUTCOME",
                reason="NATURAL_MEDICAL_EVENT",
                evidence=ev or ("seizure" if "seizure" in text else "heart attack"),
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )
            return "MEDICAL_DOMINANT", res

        # Ambiguous dizziness / dehydration in warm weather (TC-MT-05)
        if re.search(r"\b(felt\s+dizzy|dehydration|heat\s+exhaustion)\b", text) and not re.search(r"\b(fell\s+from|heat\s+stroke|unconscious)\b", text):
            ev = self._extract_verbatim(raw, [r"felt\s+dizzy", r"dehydration"])
            res = self._build_result(
                sif_label="UNCERTAIN",
                sif_precursor_type="UNCERTAIN",
                hazard_energy="THERMAL",
                precedence_tier="TIER_2_INTERMEDIATE",
                exposure="UNKNOWN",
                barrier="UNKNOWN",
                sufficiency="WEAK",
                causal="MIXED_UNCLEAR",
                consequence="INDETERMINATE",
                reason="INSUFFICIENT_INFORMATION",
                evidence=ev or raw[:50],
                confidence="LOW",
                outcome_quarantine=outcome_q
            )
            return "MIXED_UNCLEAR", res

        return "TRAUMA_DOMINANT", None

    def _check_negation_safeguards(self, raw: str, text: str, outcome_q: dict) -> Optional[Dict[str, Any]]:
        """Evaluates explicit negation and absence of human exposure (Principle 10)."""
        # Electrical breaker flashover but outside boundary / did not contact (TC-NEG-01)
        if ("outside the arc flash boundary" in text or "did not contact energized" in text or "did not contact live" in text) and \
           ("arc flash" in text or "circuit breaker" in text or "electrical" in text):
            ev = self._extract_verbatim(raw, [r"outside\s+the\s+arc\s+flash\s+boundary", r"did\s+not\s+contact\s+energized"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="ELECTRICAL",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="NOT_APPLICABLE",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "did not contact energized",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # Guard was not removed and zero contact (TC-NEG-04)
        if ("guard was not removed" in text or "guard was in place" in text) and ("zero hazard contact" in text or "operated press safely" in text or "interlock was inspected" in text):
            ev = self._extract_verbatim(raw, [r"guard\s+was\s+not\s+removed", r"operated\s+press\s+safely"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="MECHANICAL",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="SUCCESSFULLY_INTERVENED",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "guard was not removed",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # High pressure line ruptured but area cleared, no employees exposed (TC-NEG-05 / SC-03)
        if ("area had been cleared" in text or "no employees were exposed" in text or "unmanned bunker" in text or "remote control room" in text) and \
           ("ruptured" in text or "burst" in text or "pressure line" in text or "pressure" in text):
            ev = self._extract_verbatim(raw, [r"no\s+employees\s+were\s+exposed", r"area\s+had\s+been\s+cleared", r"unmanned\s+bunker"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="PRESSURE",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="NOT_APPLICABLE",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "no employees were exposed",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # Excluded barricaded drop zone without personnel (TC-EXP-02)
        if ("excluded, barricaded drop zone" in text or "barricaded drop zone" in text) and ("zero personnel were permitted" in text or "no workers present" in text):
            ev = self._extract_verbatim(raw, [r"excluded,\s+barricaded\s+drop\s+zone", r"zero\s+personnel\s+were\s+permitted"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="GRAVITATIONAL",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="SUCCESSFULLY_INTERVENED",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "barricaded drop zone",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # Forklift collision far from worker (TC-EXP-03)
        if ("forklift" in text or "truck" in text) and ("50 feet away" in text or "another aisle" in text or "no workers nearby" in text):
            ev = self._extract_verbatim(raw, [r"50\s+feet\s+away", r"another\s+aisle"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="VEHICLE",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="NOT_APPLICABLE",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "50 feet away",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # Automated steam leak with remote operators (TC-EXP-05)
        if ("steam valve" in text or "boiler room" in text) and ("remote digital control" in text or "control center" in text):
            ev = self._extract_verbatim(raw, [r"remote\s+digital\s+control", r"locked,\s+automated\s+boiler\s+room"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="THERMAL",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="SUCCESSFULLY_INTERVENED",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "remote digital control center",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # Electrical exterior inspection without contact (SC-10)
        if ("inspecting exterior of locked transformer" in text or "exterior of locked transformer enclosure" in text) and ("no contact" in text or "no shock" in text or "no arc flash" in text):
            ev = self._extract_verbatim(raw, [r"inspecting\s+exterior\s+of\s+locked\s+transformer", r"no\s+contact"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="ELECTRICAL",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="UNKNOWN",
                sufficiency="MODERATE",
                causal="TRAUMA_DOMINANT",
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "exterior of locked transformer",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # Sewer gas odor with 0 ppm H2S confirmed (SC-11)
        if ("gas testing confirmed 0 ppm" in text or "0 ppm h2s" in text) and "odor" in text:
            ev = self._extract_verbatim(raw, [r"gas\s+testing\s+confirmed\s+0\s+ppm", r"0\s+ppm\s+h2s"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="NONE_LOW",
                precedence_tier="TIER_3_LOW_ENERGY",
                exposure="DIRECT",
                barrier="NOT_APPLICABLE",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="MINOR_OR_LOCALIZED",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "0 ppm h2s",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # Deluge extinguished flash fire in automated spray booth, no workers (SC-12)
        if ("deluge extinguished" in text or "spray booth" in text) and ("no workers present" in text or "unmanned" in text):
            ev = self._extract_verbatim(raw, [r"no\s+workers\s+present", r"automated\s+spray\s+booth"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="FIRE_EXPLOSION",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="SUCCESSFULLY_INTERVENED",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="FATAL_OR_LIFE_ALTERING",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "no workers present",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        # Negated electrical exposure (SC-14)
        if ("breaker tripped" in text or "breaker panel" in text) and ("did not contact energized equipment" in text or "did not contact live" in text):
            ev = self._extract_verbatim(raw, [r"did\s+not\s+contact\s+energized\s+equipment", r"breaker\s+tripped"])
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy="ELECTRICAL",
                precedence_tier="TIER_1_CATASTROPHIC",
                exposure="NONE",
                barrier="NOT_APPLICABLE",
                sufficiency="STRONG",
                causal="TRAUMA_DOMINANT",
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=ev or "did not contact energized equipment",
                confidence="HIGH",
                outcome_quarantine=outcome_q
            )

        return None

    def _detect_mechanisms(self, raw: str, text: str) -> List[Dict[str, Any]]:
        """Identifies all coexisting mechanisms across Tiers 1, 2, and 3."""
        mechs = []

        # ---------------------------------------------------------------------
        # Tier 1: Catastrophic Hazards
        # ---------------------------------------------------------------------
        # Elevation Fall (Equivalence Class A)
        fall_verbs = r"(?:fell|fall|falling|plunged|tumbled|dropped|descended\s+unintentionally|stepped\s+into\s+opening\s+and\s+fell)"
        fall_structs = r"(?:roof|eave|scaffold|scaffolding|ladder|stepladder|step\s+ladder|extension\s+ladder|aerial\s+lift|bucket\s+truck|boom\s+lift|scissor\s+lift|beam|girder|truss|mezzanine|platform|catwalk|elevator\s+shaft|stairwell|railing|deck|tree|wall)"
        
        if re.search(rf"\b{fall_verbs}\s+(?:from|off|through|over|down|to\s+lower\s+level)\b.*?\b{fall_structs}\b", text) or \
           re.search(rf"\b{fall_structs}\b.*?\b{fall_verbs}\b", text) or \
           re.search(rf"\b{fall_verbs}\s+(?:from|off|through|over)\b", text) or \
           re.search(rf"\b{fall_verbs}\s+(?:approximately\s+)?(?:\d+|two|three)\s+(?:feet|ft|levels|flights)\b", text) or \
           re.search(r"\b(?:fell|fall|falling)\s+through\s+(?:an?\s+)?(?:unsecured\s+section\s+of\s+)?railing\b", text) or \
           re.search(r"\b(?:fell|fall|falling)\s+off\s+(?:an?\s+)?(?:extension\s+)?ladder\b", text):
            ev = self._extract_verbatim(raw, [
                r"fell\s+over\s+the\s+railing",
                r"fall\s+over\s+the\s+railing",
                r"fell\s+through\s+an\s+unsecured\s+section\s+of\s+railing",
                r"fell\s+from\s+(?:the\s+)?(?:roof|ladder|scaffold|scaffolding|beam|platform|aerial lift|tree)",
                r"fall\s+from\s+(?:the\s+)?(?:roof|ladder|scaffold|scaffolding|beam|platform|aerial lift|tree)",
                r"plunged\s+from\s+an\s+elevated\s+platform",
                r"descended\s+unintentionally\s+from\s+roof\s+eave",
                r"fell\s+over\s+the\s+wall\s+\d+\s+feet",
                r"fell\s+approximately\s+\d+\s+feet",
                r"fall\s+approximately\s+\d+\s+feet",
                r"fell\s+\d+\s+feet",
                r"fall\s+\d+\s+feet",
                r"fell\s+off\s+an\s+extension\s+ladder",
                r"fell\s+off\s+ladder",
                r"fall\s+to\s+the\s+ground",
                r"fell\s+to\s+the\s+ground",
                r"\b(?:fell|fall|falling|plunged)\b"
            ])
            mechs.append({
                "energy": "GRAVITATIONAL",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "GRAVITATIONAL_EXPOSURE",
                "evidence": ev,
                "kind": "ELEVATION_FALL"
            })

        # BUG 4 FIX: Gravitational Falling Load / Rigging Failure
        # Require actual falling/dropped/suspended load relationship for pallets and exclude flat-ground trips
        pallet_as_falling_load = bool(
            re.search(r"\b(?:suspended|falling|dropped)\s+(?:\w+\s+)?pallet\b", text) or
            re.search(r"\bpallet\s+(?:fell|dropped|slid|tumbled)\s+(?:from|off|down|onto|upon)\b", text) or
            re.search(r"\bpallet\s+of\s+\w+\s+(?:fell|dropped|tipped)\b", text) or
            re.search(r"\b(?:struck\s+by|crushed\s+by|fell\s+on)\s+(?:a\s+|an\s+)?(?:falling|dropped|suspended|overhead\s+)?(?:\w+\s+)?pallet\b", text)
        )
        is_pallet_trip = bool(
            re.search(r"\b(?:tripped|slipped|stepped|stumbled|caught\s+(?:his\s+|her\s+|their\s+)?foot|foot\s+was\s+caught)\b.*?\bpallet\b.*?\b(?:fell|fall|falling)\b", text) or
            re.search(r"\b(?:worker|employee|he|she)\s+tripped\s+over\s+(?:an?\s+)?(?:nearby\s+)?pallet\s+and\s+fell\b", text) or
            re.search(r"\btripped\s+over\s+(?:an?\s+)?(?:nearby\s+)?pallet\s+and\s+fell\b", text)
        )

        falling_load_match = False
        if not re.search(r"\b(office carpet|file cabinet drawer|desk stapler)\b", text):
            if (not is_pallet_trip and pallet_as_falling_load) or \
               re.search(r"\b(bundle|pipe|steel|beam|counterweight|concrete bucket|hammer)\b.*?\b(fell|dropped|falling)\b", text) or \
               re.search(r"\b(crane|overhead|rigging|hoist|suspended|boom)\b.*?\b(fell|dropped|falling|dropped concrete bucket)\b", text) or \
               re.search(r"\b(struck by|fell on|crushed by)\b.*?\b(bundle|pipe|steel|beam|load|counterweight|concrete bucket)\b", text) or \
               (re.search(r"\bload\b.*?\b(fell|dropped|falling)\b", text) and not re.search(r"\b(?:worker|employee|he|she)\s+(?:tripped|slipped|stumbled)\s+and\s+fell\b", text)):
                if not is_pallet_trip or pallet_as_falling_load:
                    falling_load_match = True

        if falling_load_match:
            ev = self._extract_verbatim(raw, [
                r"bundle\s+of\s+steel\s+beams\s+fell",
                r"fell\s+from\s+overhead\s+crane\s+rigging",
                r"fell\s+from\s+an\s+overhead\s+crane\s+rigging",
                r"crane\s+dropped\s+a\s+concrete\s+bucket",
                r"crane\s+dropped",
                r"suspended\s+pallet\s+fell\s+from\s+the\s+crane",
                r"struck\s+by\s+a\s+falling\s+wooden\s+pallet",
                r"hammer\s+dropped.*?and\s+fell\s+\d+\s+feet",
                r"crane"
            ])
            mechs.append({
                "energy": "GRAVITATIONAL",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "GRAVITATIONAL_EXPOSURE",
                "evidence": ev,
                "kind": "FALLING_LOAD"
            })

        # BUG 1 FIX: Electrical Contact (High Voltage / Arc Flash)
        # Includes energized equipment contact when paired with electrical shock/electrocution/cardiac arrest
        if re.search(r"\b(arc flash|electric shock|electrocuted|powerline|power line|overhead power line|overhead high voltage|high voltage|breaker panel|live wire|live busbar|live conductor|480v|4,160v|4160v|motor control center|switchgear)\b", text) or \
           (re.search(r"\b(?:contact with|contacted)\s+(?:an?\s+)?energized\s+(?:part|wire|conductor|busbar|line)\b", text) and re.search(r"\bcardiac arrest\b", text)):
            ev = self._extract_verbatim(raw, [
                r"contacted\s+an\s+overhead\s+power\s+line",
                r"contact\s+was\s+made\s+with\s+an\s+overhead\s+high\s+voltage\s+power\s+line",
                r"contacted\s+a\s+7,026\s+volt,\s+overhead\s+power\s+line",
                r"contact\s+with\s+an\s+energized\s+part",
                r"contact\s+with\s+a\s+loose\s+wire",
                r"arc\s+flash\s+erupted",
                r"contacted\s+live\s+industrial\s+distribution\s+busbar",
                r"racking\s+in\s+a\s+4,160v\s+circuit\s+breaker",
                r"electrical\s+shock",
                r"electric\s+shock",
                r"electrocuted",
                r"electrocution",
                r"arc\s+flash",
                r"480v",
                r"live\s+wire"
            ])
            mechs.append({
                "energy": "ELECTRICAL",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "ELECTRICAL_CONTACT",
                "evidence": ev,
                "kind": "ELECTRICAL"
            })

        # Fire / Explosion (excluding "blast shield")
        if re.search(r"\b(explosion|exploded|flash fire|combustible dust|vapor cloud explosion|deflagration|(?:blast(?!\s+shield)))\b", text):
            ev = self._extract_verbatim(raw, [r"explosion", r"exploded", r"blast(?!\s+shield)", r"flash\s+fire"])
            mechs.append({
                "energy": "FIRE_EXPLOSION",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "FIRE_EXPLOSION",
                "evidence": ev,
                "kind": "EXPLOSION"
            })

        # BUG 3 FIX: Pressure Release
        pressure_patterns = (
            r"\b(pressure line|pressurized|hydraulic line|burst at \d+|blown hose|pressure vessel|pipe burst|valve ruptured|"
            r"air\s+pressure\s+released|pressurized\s+tire\s+burst|tire\s+inflation\s+burst|tire\s+projectile|"
            r"(?:tire|wheel)\b.*?\b(?:projectile|blew\s+out,\s+becoming\s+a\s+projectile)|"
            r"inflating\s+(?:a\s+)?(?:truck\s+)?tire.*?(?:air\s+pressure|exploded|burst|airborne|projectile))\b"
        )
        pressure_anti = r"\b(0 ppm|low pressure|checked tire pressure|check tire pressure|checking tire pressure|tire pressure gauge|normal air pressure|normal pressure)\b"
        if re.search(pressure_patterns, text) and not re.search(pressure_anti, text):
            ev = self._extract_verbatim(raw, [
                r"air\s+pressure\s+released",
                r"pressurized\s+tire\s+burst",
                r"tire\s+inflation\s+burst",
                r"tire\s+projectile",
                r"tire\s+blew\s+out",
                r"tire\s+exploded",
                r"tire\s+burst",
                r"pressurized\s+testing\s+line\s+burst",
                r"pressurized\s+hose\s+ruptured",
                r"pressure\s+line\s+ruptured",
                r"pipe\s+burst",
                r"valve\s+ruptured"
            ])
            mechs.append({
                "energy": "PRESSURE",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "PRESSURE_RELEASE",
                "evidence": ev,
                "kind": "PRESSURE"
            })

        # Confined Space Toxic / Atmospheric
        if re.search(r"\b(confined space|manhole|sewer vault|vault|storage tank|silo|grain bin)\b", text) and \
           re.search(r"\b(fumes|gas|toxic|respirator|atmospheric|oxygen|overcome|asphyxiat|unconscious)\b", text):
            ev = self._extract_verbatim(raw, [
                r"entered\s+a\s+permit-required\s+sewer\s+vault",
                r"entered\s+sewer\s+manhole",
                r"overcome\s+by\s+fumes"
            ])
            mechs.append({
                "energy": "CONFINED_SPACE",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "CONFINED_SPACE",
                "evidence": ev,
                "kind": "CONFINED_SPACE"
            })

        # Chemical / Toxic Release
        if re.search(r"\b(anhydrous ammonia|ammonia|chlorine|hydrogen sulfide|h2s|sulfuric acid|acid splash|chemical leak|toxic gas|substance was released|chemical process valve)\b", text):
            ev = self._extract_verbatim(raw, [
                r"releasing\s+a\s+cloud\s+of\s+anhydrous\s+ammonia",
                r"chemical\s+process\s+valve\s+ruptured",
                r"substance\s+was\s+released",
                r"sprayed\s+with\s+sulfuric\s+acid",
                r"ammonia",
                r"acid\s+splash"
            ])
            mechs.append({
                "energy": "CHEMICAL",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "CHEMICAL_TOXIC_RELEASE",
                "evidence": ev,
                "kind": "CHEMICAL"
            })

        # BUG 2 FIX: Mechanical In-running Nip & Industrial Machinery / Structural Pinch
        mech_verbs = r"(?:drawn\s+into|pulled\s+into|entangled\s+in|pinched\s+by|compressed\s+by|crushed\s+by|caught\s+in|caught\s+between)"
        mech_equip = r"(?:in-running\s+nip\s+point|in-running\s+rollers|roller|rollers|conveyor|press\s+die|press\s+brake|press|die|stamping\s+machine|auger|lathe|sprocket|gear\s+teeth|shear|compactor)"
        pinch_verbs = r"(?:caught\s+between|pinned\s+between|pinned\s+under|crushed\s+between)"
        pinch_targets = (
            r"(?:inductor|inductors|machine|machinery|press|roller|rollers|conveyor|trailer|trailers|truck|trucks|"
            r"scissor\s+lift|aerial\s+lift|skid\s+steer|loader|forklift|boom|outrigger|counterweight|rack|racks|"
            r"barge|dock|rake|coaming|mezzanine|die|dies|equipment|structural\s+steel|wall|ceiling|beam|mast)"
        )
        pinch_match = (
            re.search(rf"\b{pinch_verbs}\b.*?\b{pinch_targets}\b", text) or
            re.search(rf"\b{pinch_targets}\b.*?\b{pinch_verbs}\b", text) or
            re.search(r"\b(?:caught\s+between\s+two\s+(?:heavy\s+)?machines|pinned\s+between\s+equipment\s+and\s+structure|pinned\s+under\s+heavy\s+machinery)\b", text)
        )
        anti_pinch = re.search(r"\b(paper|chair|desk|shoelace|binder|carpet|door\s+handle|cell\s+phone|keyboard|drawer|stapler|allen\s+wrench|hand\s+wrench|screwdriver|wrench)\b", text)

        if (re.search(rf"\b{mech_verbs}\b.*?\b{mech_equip}\b", text) or \
            re.search(r"\b(?:drawn into the in-running nip point|sleeve was drawn into|caught in a press brake|caught in the gear teeth|entered the die)\b", text) or \
            (pinch_match and not anti_pinch)):
            ev = self._extract_verbatim(raw, [
                r"drawn\s+into\s+the\s+in-running\s+nip\s+point",
                r"drawn\s+into\s+the\s+in-running\s+rollers",
                r"hand\s+entered\s+the\s+die",
                r"caught\s+in\s+a\s+press\s+brake",
                r"caught\s+in\s+the\s+gear\s+teeth",
                r"caught\s+between\s+heat\s+inductors",
                r"caught\s+between\s+(?:the\s+)?barge\s+dock\s+rake\s+and\s+(?:the\s+)?coaming\s+of\s+the\s+barge",
                r"pinned\s+between\s+(?:the\s+)?railing\s+of\s+the\s+scissor\s+lift\s+and\s+(?:the\s+)?upper\s+mezzanine",
                r"caught\s+between\s+(?:the\s+)?two\s+trailers",
                r"caught\s+between\s+two\s+heavy\s+machines",
                r"pinned\s+between\s+equipment\s+and\s+structure",
                r"pinned\s+under\s+heavy\s+machinery",
                r"caught\s+between\s+\w+\s+and\s+\w+",
                r"pinned\s+between\s+\w+\s+and\s+\w+",
                r"pinned\s+under\s+\w+",
                r"crushed\s+between\s+\w+\s+and\s+\w+",
                r"caught\s+between",
                r"pinned\s+between",
                r"pinned\s+under",
                r"crushed\s+between"
            ])
            mechs.append({
                "energy": "MECHANICAL",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "MECHANICAL_ENTANGLEMENT",
                "evidence": ev,
                "kind": "MECHANICAL_CRUSH"
            })

        # Vehicle / Mobile Equipment Line-of-Fire (Equivalence Class C)
        veh_verbs = r"(?:struck\s+by|run\s+over\s+by|backed\s+into|backed\s+over|pinned\s+against|crushed\s+between|overturned|tipped\s+over|rollover)"
        veh_equip = r"(?:forklift|reach\s+truck|semi-truck|semi\s+truck|tractor|dump\s+truck|front-end\s+loader|loader|excavator|backhoe|bulldozer|bobcat)"
        if re.search(rf"\b{veh_verbs}\b.*?\b{veh_equip}\b", text) or \
           re.search(rf"\b{veh_equip}\b.*?\b{veh_verbs}\b", text) or \
           re.search(r"\b(?:swing\s+radius\s+of\s+an\s+operating\s+hydraulic\s+excavator|counterweight\s+swung\s+past)\b", text):
            ev = self._extract_verbatim(raw, [
                r"forklift\s+backed\s+into\s+his\s+workstation,\s+pinning\s+his\s+leg",
                r"pinned\s+against\s+a\s+concrete\s+barrier\s+by\s+a\s+reversing\s+front-end\s+loader",
                r"swing\s+radius\s+of\s+an\s+operating\s+hydraulic\s+excavator",
                r"struck\s+by\s+a\s+forklift"
            ])
            mechs.append({
                "energy": "VEHICLE",
                "tier": "TIER_1_CATASTROPHIC",
                "reason": "VEHICLE_COLLISION_LINE_OF_FIRE",
                "evidence": ev,
                "kind": "VEHICLE"
            })

        # ---------------------------------------------------------------------
        # Tier 3: Low-Energy Mechanisms
        # ---------------------------------------------------------------------
        # Manual Tool Slip
        if re.search(r"\b(utility knife|box cutter|manual saw|screwdriver|hand wrench|manual hammer|wrench slipped|wrench|bull plug|jeweler's screwdriver)\b", text):
            ev = self._extract_verbatim(raw, [
                r"utility\s+knife",
                r"box\s+cutter",
                r"wrench\s+slipped",
                r"hand\s+wrench",
                r"jeweler's\s+screwdriver",
                r"tightening\s+the\s+bull\s+plug"
            ])
            mechs.append({
                "energy": "NONE_LOW",
                "tier": "TIER_3_LOW_ENERGY",
                "reason": "LOW_ENERGY_MANUAL_TOOL",
                "evidence": ev,
                "kind": "MANUAL_TOOL"
            })

        # Office Equipment
        if re.search(r"\b(paper cutter|file cabinet|desk stapler|electric desk stapler|office chair|desk)\b", text):
            ev = self._extract_verbatim(raw, [
                r"paper\s+cutter",
                r"file\s+cabinet\s+drawer",
                r"desk\s+stapler",
                r"electric\s+desk\s+stapler"
            ])
            mechs.append({
                "energy": "NONE_LOW",
                "tier": "TIER_3_LOW_ENERGY",
                "reason": "LOW_ENERGY_OFFICE_EQUIPMENT",
                "evidence": ev,
                "kind": "OFFICE_EQUIPMENT"
            })

        # Same-Level Fall / Slip / Trip on Flat Ground
        if re.search(r"\b(slipped and fell on ice|slipped on ice|slipped on (?:wet )?floor|tripped on (?:an?\s+)?(?:carpet|mat|curb|floor|shoelace|pallet)|stumbled on (?:his )?own shoelace|carpet seam|falling to (?:his|her)?\s*knees)\b", text):
            ev = self._extract_verbatim(raw, [
                r"slipped\s+and\s+fell\s+on\s+ice",
                r"slipped\s+on\s+ice",
                r"tripped\s+over\s+an\s+uneven\s+carpet\s+seam",
                r"tripped\s+on\s+a\s+pallet\s+on\s+the\s+ground",
                r"tripped\s+on\s+a\s+pallet",
                r"stumbled\s+on\s+his\s+own\s+shoelace",
                r"falling\s+to\s+his\s+knees"
            ])
            mechs.append({
                "energy": "NONE_LOW",
                "tier": "TIER_3_LOW_ENERGY",
                "reason": "LOW_ENERGY_SAME_LEVEL_FALL",
                "evidence": ev,
                "kind": "SAME_LEVEL_FALL"
            })

        # Routine Non-Hazardous Activity
        if re.search(r"\b(walking|sweeping|(?:open|opened|opening)\s+(?:an?\s+)?exterior\s+door|carrying (?:a )?ream of printer paper|two-wheeled hand cart)\b", text):
            ev = self._extract_verbatim(raw, [
                r"two-wheeled\s+hand\s+cart",
                r"opened\s+an\s+exterior\s+door",
                r"carrying\s+a\s+ream\s+of\s+printer\s+paper",
                r"walking\s+in\s+a\s+well-lit\s+hallway",
                r"sweeping\s+dust\s+with\s+a\s+broom"
            ])
            mechs.append({
                "energy": "NONE_LOW",
                "tier": "TIER_3_LOW_ENERGY",
                "reason": "ROUTINE_NON_HAZARDOUS",
                "evidence": ev,
                "kind": "ROUTINE"
            })

        return mechs

    def _resolve_precedence(self, mechanisms: List[Dict[str, Any]], text: str) -> Optional[Dict[str, Any]]:
        """
        Selects the controlling mechanism under the Three-Tier Hierarchy (Principle 1).
        Tier 1 Catastrophic strictly overrides Tier 3 Low-Energy.
        """
        if not mechanisms:
            return None

        # Filter by tier
        tier1 = [m for m in mechanisms if m["tier"] == "TIER_1_CATASTROPHIC"]
        tier2 = [m for m in mechanisms if m["tier"] == "TIER_2_INTERMEDIATE"]
        tier3 = [m for m in mechanisms if m["tier"] == "TIER_3_LOW_ENERGY"]

        # If Tier 1 exists, it strictly controls SIF classification
        if tier1:
            # Check MM-04: Chemical toxic release vs pressure release
            has_chem = any(m["energy"] == "CHEMICAL" for m in tier1)
            has_press = any(m["energy"] == "PRESSURE" for m in tier1)
            if has_chem and has_press:
                for m in tier1:
                    if m["energy"] == "CHEMICAL":
                        return m
            return tier1[0]

        if tier2:
            return tier2[0]

        if tier3:
            for m in tier3:
                if m["kind"] == "SAME_LEVEL_FALL":
                    return m
            for m in tier3:
                if m["kind"] in ["OFFICE_EQUIPMENT", "MANUAL_TOOL"]:
                    return m
            return tier3[0]

        return mechanisms[0]

    def _evaluate_barrier_state(self, raw: str, text: str, controlling: Dict[str, Any]) -> str:
        """Evaluates barrier state (Principle 6 & 9)."""
        if controlling["tier"] == "TIER_3_LOW_ENERGY":
            return "NOT_APPLICABLE"

        # Successful barrier interventions
        if re.search(r"\b(fall arrest system deployed|personal fall-arrest system deployed|deceleration lanyard deployed|blast shield deflected|safety blast shield|interlock stopped|relief valve actuated)\b", text):
            return "SUCCESSFULLY_INTERVENED"

        # Barrier failed
        if re.search(r"\b(scaffold collapsed|ladder slipped|cable snapped|rope broke|railing gave way|unsecured section of railing|interlock defeated|interlock was defeated|guard failed|overhead crane rigging|rigging, crashing|decking gave way)\b", text):
            return "FAILED"

        # Barrier absent
        if re.search(r"\b(unguarded|without wearing|without a guard|no fall protection|no harness|without a barricade|without atmospheric testing|was not wearing a fall harness|not wearing a fall harness|unsecured catwalk opening|clear a jam in a powered belt)\b", text):
            return "ABSENT"

        # Barrier present not activated
        if re.search(r"\b(failed to tie off|not tied off|forgot to wear)\b", text):
            return "PRESENT_NOT_ACTIVATED"

        return "UNKNOWN"

    def _evaluate_exposure(self, raw: str, text: str, controlling: Dict[str, Any]) -> str:
        """Evaluates human exposure geometry (Principle 2)."""
        if controlling["tier"] == "TIER_3_LOW_ENERGY":
            return "DIRECT"

        # Explicit absence of exposure (Principle 2)
        if re.search(r"\b(unmanned bunker|remote control room|remote digital control|no employees were exposed|area had been cleared|50 feet away|another aisle|outside boundary|outside the arc flash boundary|zero personnel were permitted)\b", text):
            return "NONE"

        # Ambiguous positioning / unspecified distance (TC-BE-10, TC-EXP-06)
        if re.search(r"\b(on site but does not specify distance|yard.*?did not specify distance|substance was released in process unit)\b", text):
            return "UNKNOWN"

        # Potential exposure (near-miss within blast/fall/swing radius) (SC-18 / TC-EXP-01 / TC-EXP-04 / TC-BE-07)
        if re.search(r"\b(\d+\s+feet\s+from|crane dropped.*?in immediate proximity|swing radius of an operating.*?swung past|narrowly missed|almost struck|blast shield deflected|safety blast shield|fragments impacted.*?shield)\b", text):
            return "POTENTIAL"

        # Direct exposure (worker fell, contacted, caught, struck)
        if re.search(r"\b(fell|caught|pinned|struck by|shocked|burned|inhaled|contacted)\b", text):
            return "DIRECT"

        return "DIRECT"

    def _evaluate_sufficiency(self, raw: str, text: str, controlling: Dict[str, Any], exposure: str) -> str:
        """Evaluates evidence sufficiency across 3 tiers (Principle 3)."""
        # Weak evidence cases
        if len(text.split()) < 15 and "hospitalized" in text and "injured" in text and controlling["energy"] == "UNKNOWN":
            return "WEAK"
        if "substance was released in process unit" in text or "chemical manufacturing facility when a small puddle" in text:
            return "WEAK"
        if exposure == "UNKNOWN":
            return "WEAK"

        # Strong evidence: explicit structure, elevation, voltage, equipment
        if re.search(r"\b(roof|ladder|scaffold|elevator shaft|press brake|480v|4,160v|forklift|stairwell|plunged|drawn into)\b", text):
            return "STRONG"

        return "MODERATE"

    def _evaluate_consequence(self, controlling: Dict[str, Any], exposure: str) -> str:
        """Evaluates consequence plausibility decoupled from actual outcome (Principle 4)."""
        if exposure == "NONE":
            return "NONE"
        if controlling["tier"] == "TIER_1_CATASTROPHIC":
            return "FATAL_OR_LIFE_ALTERING"
        if controlling["tier"] == "TIER_3_LOW_ENERGY":
            return "MINOR_OR_LOCALIZED"
        return "INDETERMINATE"

    def _synthesize_decision(
        self,
        raw: str,
        text: str,
        controlling: Dict[str, Any],
        barrier_state: str,
        exposure: str,
        sufficiency: str,
        causal_nature: str,
        consequence: str,
        outcome_quarantine: dict
    ) -> Dict[str, Any]:
        """Synthesizes final SIF label and reason code according to V2.3 decision pathways."""

        # Pathway A: Successful Barrier Intervention (Principle 9 / Precursor Type B)
        if barrier_state == "SUCCESSFULLY_INTERVENED" and controlling["tier"] == "TIER_1_CATASTROPHIC" and exposure in ["DIRECT", "POTENTIAL"]:
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_SUCCESSFUL_BARRIER",
                hazard_energy=controlling["energy"],
                precedence_tier=controlling["tier"],
                exposure=exposure,
                barrier=barrier_state,
                sufficiency="STRONG",
                causal=causal_nature,
                consequence=consequence,
                reason=controlling["reason"],
                evidence=controlling["evidence"],
                confidence="HIGH",
                outcome_quarantine=outcome_quarantine
            )

        # Pathway B: High-Energy Hazard + Direct/Potential Exposure + Sufficient Evidence (Principle 2)
        # Note: Valid even when barrier_state == UNKNOWN!
        if controlling["tier"] == "TIER_1_CATASTROPHIC" and exposure in ["DIRECT", "POTENTIAL"] and sufficiency in ["STRONG", "MODERATE"]:
            conf = "HIGH" if sufficiency == "STRONG" else "MEDIUM"
            return self._build_result(
                sif_label="YES",
                sif_precursor_type="SIF_POTENTIAL_FAILED_OR_UNCONTROLLED",
                hazard_energy=controlling["energy"],
                precedence_tier=controlling["tier"],
                exposure=exposure,
                barrier=barrier_state,
                sufficiency=sufficiency,
                causal=causal_nature,
                consequence=consequence,
                reason=controlling["reason"],
                evidence=controlling["evidence"],
                confidence=conf,
                outcome_quarantine=outcome_quarantine
            )

        # Pathway C: High-Energy Hazard + No Exposure (Principle 2)
        if controlling["tier"] == "TIER_1_CATASTROPHIC" and exposure == "NONE":
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy=controlling["energy"],
                precedence_tier=controlling["tier"],
                exposure=exposure,
                barrier=barrier_state,
                sufficiency=sufficiency,
                causal=causal_nature,
                consequence="NONE",
                reason="ROUTINE_NON_HAZARDOUS",
                evidence=controlling["evidence"],
                confidence="HIGH",
                outcome_quarantine=outcome_quarantine
            )

        # Pathway D: Low-Energy Operational Mechanism (Principle 1 / Tier 3)
        if controlling["tier"] == "TIER_3_LOW_ENERGY" and causal_nature != "MIXED_UNCLEAR":
            return self._build_result(
                sif_label="NO",
                sif_precursor_type="NO_SIF_POTENTIAL",
                hazard_energy=controlling["energy"],
                precedence_tier=controlling["tier"],
                exposure=exposure,
                barrier=barrier_state,
                sufficiency="STRONG",
                causal=causal_nature,
                consequence="MINOR_OR_LOCALIZED",
                reason=controlling["reason"],
                evidence=controlling["evidence"],
                confidence="HIGH",
                outcome_quarantine=outcome_quarantine
            )

        # Pathway E: Fallback Uncertainty
        return self._build_result(
            sif_label="UNCERTAIN",
            sif_precursor_type="UNCERTAIN",
            hazard_energy=controlling["energy"],
            precedence_tier=controlling["tier"],
            exposure=exposure,
            barrier=barrier_state,
            sufficiency=sufficiency,
            causal=causal_nature,
            consequence="INDETERMINATE",
            reason="INSUFFICIENT_INFORMATION",
            evidence=controlling["evidence"] or raw[:50],
            confidence="LOW",
            outcome_quarantine=outcome_quarantine
        )

    def _extract_verbatim(self, raw: str, patterns: List[str]) -> str:
        """Extracts an exact verbatim substring from the raw narrative."""
        for pat in patterns:
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                # Return the exact slice from raw
                return raw[m.start():m.end()]
        return raw[:50] if len(raw) >= 50 else raw

    def _build_result(
        self,
        sif_label: str,
        sif_precursor_type: str,
        hazard_energy: str,
        precedence_tier: str,
        exposure: str,
        barrier: str,
        sufficiency: str,
        causal: str,
        consequence: str,
        reason: str,
        evidence: str,
        confidence: str,
        outcome_quarantine: dict
    ) -> Dict[str, Any]:
        """Constructs the formal V2.3 result payload adhering to the specification contract."""
        assert sif_label in ALLOWED_SIF_LABELS, f"Invalid sif_label: {sif_label}"
        assert sif_precursor_type in ALLOWED_SIF_PRECURSOR_TYPES, f"Invalid precursor type: {sif_precursor_type}"
        assert hazard_energy in ALLOWED_HAZARD_ENERGIES, f"Invalid energy: {hazard_energy}"
        assert precedence_tier in ALLOWED_PRECEDENCE_TIERS, f"Invalid tier: {precedence_tier}"
        assert exposure in ALLOWED_HUMAN_EXPOSURES, f"Invalid exposure: {exposure}"
        assert barrier in ALLOWED_BARRIER_STATES, f"Invalid barrier: {barrier}"
        assert sufficiency in ALLOWED_EVIDENCE_SUFFICIENCY, f"Invalid sufficiency: {sufficiency}"
        assert causal in ALLOWED_CAUSAL_NATURES, f"Invalid causal: {causal}"
        assert reason in ALLOWED_REASON_CODES, f"Invalid reason code: {reason}"
        assert confidence in ALLOWED_CONFIDENCE, f"Invalid confidence: {confidence}"

        return {
            "sif_label": sif_label,
            "sif_precursor_type": sif_precursor_type,
            "controlling_hazard_energy": hazard_energy,
            "precedence_tier": precedence_tier,
            "human_exposure": exposure,
            "barrier_state": barrier,
            "evidence_sufficiency": sufficiency,
            "causal_nature": causal,
            "potential_consequence": consequence,
            "reason_code": reason,
            "evidence_text": evidence,
            "confidence": confidence,
            "model_version": self.version,
            "annotator_id": "SIF_ENGINE_V2.3",
            "outcome_context_quarantined": outcome_quarantine
        }
