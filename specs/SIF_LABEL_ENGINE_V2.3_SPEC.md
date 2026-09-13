# SIF Label Engine V2.3: Narrative-Only Engineering Specification
## SIH26165 — AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors in Safety Reports

**Specification Version:** 2.3.0-SPEC-DESIGN  
**Status:** SPECIFICATION DESIGN ONLY (FROZEN BASELINE PRESERVED)  
**Date:** September 13, 2026  
**Supersedes:** `SIF_LABEL_ENGINE_V2_SPEC.md` (Version 2.0 / 2.2)  
**Implementation Phase:** SPECIFICATION ONLY — NO CODE MODIFICATION PERMITTED IN THIS PHASE  

---

## Executive Summary & System Mandate

The **SIF Label Engine V2.3** specification establishes a formal, evidence-based, deterministic safety-reasoning architecture designed to detect **Serious Injury and Fatality (SIF) Precursors** exclusively from unstructured text narratives. 

V2.3 directly resolves the confirmed engineering issues identified during the **Phase 4B Forensic Audit** (`ISSUE-V2-001` through `ISSUE-V2-005`):
1. **Rule Precedence Collision (`ISSUE-V2-001`):** Resolves the defect where early low-energy manual tool detection preempted severe gravitational falls (e.g. `PILOT_075`, `PILOT_076`).
2. **Barrier Evidence Over-Coupling (`ISSUE-V2-002`):** Corrects the false assumption that missing barrier mentions require defaulting to `UNCERTAIN` when physical hazard energy and direct human exposure already prove credible SIF potential.
3. **Syntactic Coverage Narrowness (`ISSUE-V2-003`):** Introduces generalized semantic equivalence classes for elevation falls, caught-in machinery, and mobile plant kinematics to accommodate natural OSHA abstract phrasings.
4. **Medical-vs-Trauma Ambiguity (`ISSUE-V2-004`):** Establishes an explicit three-class causal taxonomy (`TRAUMA_DOMINANT`, `MEDICAL_DOMINANT`, `MIXED_UNCLEAR`) for complex delayed events (e.g. `PILOT_084`).
5. **Outcome Bias Vulnerability (`ISSUE-V2-005`):** Enforces strict two-channel quarantine isolating physical precursor evidence from medical aftermath keywords.

> [!IMPORTANT]
> **Governance & Implementation Freeze**
> * This document is a **specification design contract only**.
> * The V2 implementation (`sif_auto_annotator_v2.py`), the frozen dataset (`sif_annotations_v2.csv`), and the regression test suite (`tests/test_sif_engine_v2.py`) remain completely unmodified and frozen.
> * Machine learning / Transformer retraining remains **strictly blocked** until double-blind human expert validation is completed against this specification.

---

## 1. Core Architectural Tenets (Preserved Baseline)

V2.3 preserves the ten foundational tenets established in V2.0:

1. **Precursor $\ne$ Outcome:** A SIF precursor is a high-energy situation with credible potential for fatal or life-altering harm. Actual injury severity is an outcome metric, not a precursor definition.
2. **Severe Outcome Decoupling:** Actual death, hospitalization, amputation, fracture, or surgery does **not** independently establish SIF precursor status.
3. **Missing Barrier $\ne$ Failed Barrier:** Narrative silence regarding safety controls must be classified as `barrier_state = UNKNOWN`. It must never be assumed to be `FAILED` or `ABSENT`.
4. **Barrier Failure Is Not Mandatory:** A documented barrier failure ($B_{\text{fail}}$) is not required for a `YES` decision when an uncontrolled high-consequence exposure is clearly documented.
5. **6-State Barrier Taxonomy:** Retains the complete barrier state taxonomy: `FAILED`, `SUCCESSFULLY_INTERVENED`, `ABSENT`, `PRESENT_NOT_ACTIVATED`, `UNKNOWN`, and `NOT_APPLICABLE`.
6. **No Arbitrary Numerical Gates:** Numerical fall heights (e.g. 6 ft), voltages (e.g. 50 V), or pressures (e.g. 100 psi) are supporting evidence within physical context, not arbitrary universal Boolean gates.
7. **Precursor Detector, Not Compliance Checker:** The engine assesses physical hazard kinematics and human vulnerability, not OSHA regulatory citations.
8. **Physical Reasoning Over Keywords:** Decisions must be derived from the physical event chain and exposure mechanics, not the presence of isolated words.
9. **Independent LSR Tagging:** Multi-label Life-Saving Rule tagging remains an orthogonal contextual layer separate from the primary SIF classification.
10. **Provisional Automated Status:** All automated labels remain provisional proxy classifications until validated by qualified human safety professionals.

---

## 2. The 10 New V2.3 Principles

### Principle 1: Multiple-Mechanism Precedence Hierarchy
Narratives frequently describe multi-event sequences (e.g., "Worker was tightening a pipe with a wrench, lost balance, and fell 14 feet from a scaffold"). Low-energy initiating mechanisms must never suppress high-energy terminal hazards.

When multiple mechanisms coexist, the engine evaluates mechanisms according to a **Three-Tier Precedence Hierarchy**:
* **Tier 1 (Catastrophic / High-Consequence Hazards):**
  * Falls from elevation ($\ge$ elevated work surfaces, roofs, scaffolds, high ladders, open edges, elevator shafts).
  * Uncontrolled gravitational collapse or suspended falling loads.
  * Electrical contact with energized industrial conductors, busbars, overhead power lines, or arc flash.
  * High-pressure pneumatic, hydraulic, or process vessel explosive release.
  * Deflagrations, flash fires, vapor cloud explosions, combustible dust fires.
  * Confined space hazardous, toxic, or oxygen-deficient atmospheres.
  * Powered machinery in-running nip points, augers, conveyor drives, industrial press dies.
  * Heavy mobile plant line-of-fire, vehicle collisions, struck-by/pinned by moving equipment.
* **Tier 2 (Intermediate Operational Hazards):**
  * Low-height falls ($<4$ feet) onto flat, non-hazardous surfaces.
  * Moderate non-powered pinch points (doors, lids, non-powered carts).
  * Pressurized spray washers or low-pressure hoses without shrapnel.
  * Contact with hot pipes or minor thermal sources without open flame.
* **Tier 3 (Low-Energy Non-SIF Mechanisms):**
  * Manual hand tool slips (utility knives, screwdrivers, manual hand saws, wrenches).
  * Low-energy office equipment (paper cutters, file cabinets, staplers, office chairs).
  * Ordinary same-level slips and trips on flat floors, carpet, or ice.
  * Routine manual lifting, carrying, or non-hazardous ergonomic handling.

> **Precedence Rule:** The mechanism assigned the highest tier that directly contributes to worker exposure or consequence governs the primary SIF classification and reason code. Tier 3 mechanisms cannot veto Tier 1 hazards.

---

### Principle 2: Energy + Exposure Can Be Sufficient
Barrier state is supporting diagnostic evidence, **not an obligatory gatekeeper**. 

The engine implements three distinct decision pathways:
$$\text{HIGH\_CONSEQUENCE\_MECHANISM} \wedge \text{CREDIBLE\_HUMAN\_EXPOSURE} \wedge \text{SUFFICIENT\_EVIDENCE} \implies \text{SIF\_YES}$$
*(Valid even when $\text{BARRIER\_STATE} = \text{UNKNOWN}$, provided no functioning barrier is indicated).*

$$\text{HIGH\_CONSEQUENCE\_MECHANISM} \wedge \text{UNCLEAR\_HUMAN\_EXPOSURE} \implies \text{SIF\_UNCERTAIN}$$

$$\text{HIGH\_CONSEQUENCE\_MECHANISM} \wedge \text{EXPLICIT\_NO\_EXPOSURE} \implies \text{SIF\_NO}$$

---

### Principle 3: Formal Evidence Sufficiency Framework
Evidence sufficiency is evaluated across three discrete, auditable tiers:

| Sufficiency Tier | Textual Characteristics | Decision Permissibility |
|---|---|---|
| **STRONG EVIDENCE** | Explicit physical mechanism, unambiguous worker location/exposure, clear interaction dynamics, explicit elevated structure/voltage/crush point documented. | Eligible for confident **`YES`** or **`NO`**. |
| **MODERATE EVIDENCE** | Mechanism and exposure strongly supported by narrative context, but minor physical parameters (exact height, exact tool model) are implicit. | Eligible for **`YES`** (with `MEDIUM` confidence) or **`NO`**. |
| **WEAK EVIDENCE** | Sparse narrative, generic keywords only, outcome mentioned without operational mechanism, or ambiguous worker positioning. | **Strictly `UNCERTAIN`**. Cannot declare `YES` or `NO`. |

---

### Principle 4: Consequence Credibility vs. Actual Outcome
The engine strictly dissociates **Actual Outcome** from **Potential Consequence**:
* **Actual Outcome:** What physically happened to the worker in this specific event (e.g., zero injury, minor abrasion, fractured tibia, fatality).
* **Potential Consequence:** The realistic, plausible worst-case harm that could occur under slightly varied circumstances (e.g., fall from 20 feet carries fatal potential even if worker survived; tripping on carpet carries non-fatal potential even if worker broke a bone).
* **Rule:** If the physical mechanism lacks the kinetic, electrical, chemical, or thermal capacity to cause permanent life-altering harm or death, the event is `NO` or `UNCERTAIN`, regardless of surgery or hospitalization.

---

### Principle 5: Medical-vs-Trauma Causal Taxonomy
To resolve ambiguous cases like `PILOT_084`, the engine classifies incidents into three causal streams:
1. **`TRAUMA_DOMINANT`:** Physical occupational energy is the direct proximate cause of harm (e.g., struck by vehicle, fall from scaffold, caught in conveyor).
2. **`MEDICAL_DOMINANT`:** An internal physiological event occurred spontaneously without traumatic workplace initiation (e.g., heart attack while sitting at desk, stroke, diabetic collapse on flat ground). Label: `NO` (`NATURAL_MEDICAL_EVENT`).
3. **`MIXED_UNCLEAR`:** Narrative describes both a physical event and a severe medical outcome where causality is ambiguous or delayed (e.g., worker struck by forklift, then suffered fatal heart attack at home 19 hours later; worker collapsed while working in hot building). Label: **`UNCERTAIN`** (`INSUFFICIENT_INFORMATION`) with explicit note requiring clinical review.

---

### Principle 6: Multi-Event Chain Representation
Narratives are modeled as an event chain:
$$\text{Initiating Event } (E_1) \longrightarrow \text{Intermediate Event } (E_2) \longrightarrow \text{Terminal Hazard } (E_3) \longrightarrow \text{Outcome } (C)$$
* In `PILOT_075`: $E_1 = \text{wrench slipped}$ (Tier 3) $\rightarrow E_2 = \text{loss of balance on stepladder}$ (Tier 2) $\rightarrow E_3 = \text{fall over stairwell railing down two levels}$ (Tier 1) $\rightarrow C = \text{punctured lung}$.
* **Controlling Mechanism:** The terminal hazard $E_3$ (Gravitational Fall from Elevation) controls classification. Reason code: `GRAVITATIONAL_EXPOSURE`. Label: `YES`.

---

### Principle 7: Semantic Equivalence Classes for Natural OSHA Phrasing
To eliminate syntactic narrowness (`ISSUE-V2-003`), the engine defines normalized semantic equivalence classes:

#### Equivalence Class A: Elevation Falls
* Phrasings: `fell from`, `fell off`, `fell through`, `fell over`, `fell to lower level`, `dropped to lower level`, `descended unintentionally`, `plunged from`, `tumbled from`, `stepped into opening and fell`, `railing gave way and fell`.
* Structures: `roof`, `eave`, `scaffold`, `scaffolding`, `ladder`, `stepladder`, `extension ladder`, `aerial lift`, `bucket truck`, `boom lift`, `scissor lift`, `beam`, `girder`, `truss`, `mezzanine`, `platform`, `catwalk`, `elevator shaft`, `stairwell`, `deck`, `tree`.

#### Equivalence Class B: Mechanical In-Running Nip & Crush
* Phrasings: `caught in`, `caught between`, `drawn into`, `pulled into`, `entangled in`, `pinched by`, `compressed by`, `crushed by`, `trapped between`, `nipped by`.
* Equipment: `roller`, `rollers`, `conveyor`, `auger`, `press die`, `press brake`, `stamping machine`, `lathe`, `sprocket`, `pulley`, `gear`, `shear`, `compactor`.

#### Equivalence Class C: Mobile Equipment Line-of-Fire
* Phrasings: `struck by`, `run over by`, `backed over by`, `pinned against`, `crushed between`, `overturned`, `tipped over`, `rollover`, `struck by falling load from`.
* Equipment: `forklift`, `reach truck`, `order picker`, `semi-truck`, `tractor-trailer`, `dump truck`, `front-end loader`, `skid-steer`, `bobcat`, `excavator`, `backhoe`, `bulldozer`.

---

### Principle 8: Two-Channel Architecture (Outcome Quarantine)
The engine maintains two strictly isolated data channels:
1. **Precursor Evidence Channel:** Processes hazard energy, physical mechanisms, exposure geometry, barrier status, and environmental conditions. **This channel exclusively drives the SIF label.**
2. **Outcome Context Channel:** Ingests outcome keywords (death, fatal, amputation, fracture, surgery, hospitalization) for clinical context, auditing, and explainability reporting. **This channel is strictly prohibited from voting on or overriding the SIF label.**

---

### Principle 9: Explicit Handling of Successful Barrier Interventions
* When a high-consequence hazard release occurs but a personal fall arrest harness, machine interlock, blast shield, or emergency shutdown successfully prevents catastrophic harm, the event is classified as:
  * `sif_label = YES`
  * `sif_precursor_type = SIF_POTENTIAL_SUCCESSFUL_BARRIER`
  * `barrier_state = SUCCESSFULLY_INTERVENED`
* A successful barrier confirms that a serious hazard existed; it must never be converted into a `NO`.

---

### Principle 10: The Anti-Assumption Axioms ("Unknown Must Remain Unknown")
The engine enforces 10 strict negative axioms:
1. **NOT MENTIONED $\ne$ FAILED:** Silence on safety barriers never implies the barrier failed.
2. **NOT MENTIONED $\ne$ ABSENT:** Silence on barriers never implies no barrier existed.
3. **WORKER PRESENT $\ne$ DIRECTLY EXPOSED:** Being in the same plant/facility does not establish line-of-fire.
4. **INJURED $\ne$ SIF PRECURSOR:** Medical harm does not prove precursor kinematics.
5. **HOSPITALIZED $\ne$ SIF PRECURSOR:** Hospital admission does not prove high-energy mechanisms.
6. **FATAL $\ne$ SIF PRECURSOR:** Natural death or non-occupational death does not prove a workplace precursor.
7. **MACHINE MENTION $\ne$ HIGH ENERGY:** Office equipment or hand tools are not industrial machinery.
8. **FALL MENTION $\ne$ ELEVATION HAZARD:** Flat-ground slips are not elevation falls.
9. **GAS MENTION $\ne$ TOXIC ATMOSPHERE:** Benign gas or compressed air is not toxic release.
10. **ELECTRICAL MENTION $\ne$ HIGH VOLTAGE CONTACT:** Changing a lightbulb is not 480V arc flash.

---

## 3. Allowed Input & Metadata Quarantine

The engine accepts **ONLY** unstructured narrative text:
* Primary Input: `normalized_narrative` (or raw narrative text).
* **Quarantined Metadata (Strictly Prohibited from Inference Pipeline):**
  * `source_event_title`
  * `source_event_code`
  * `hazard_stratum`
  * `source_nature_title`
  * `source_part_title`
  * `hospitalized` (structured flag)
  * `amputation` (structured flag)
  * `inspection_id`
  * `sampling_stratum`

---

## 4. Controlled Vocabularies & Ontology

### 4.1 Hazard / Energy Categories (11)
`GRAVITATIONAL`, `ELECTRICAL`, `MECHANICAL`, `PRESSURE`, `CHEMICAL`, `THERMAL`, `VEHICLE`, `FIRE_EXPLOSION`, `CONFINED_SPACE`, `NONE_LOW`, `UNKNOWN`.

### 4.2 Human Exposure States (4)
`DIRECT`, `POTENTIAL`, `NONE`, `UNKNOWN`.

### 4.3 Barrier States (6)
`FAILED`, `SUCCESSFULLY_INTERVENED`, `ABSENT`, `PRESENT_NOT_ACTIVATED`, `UNKNOWN`, `NOT_APPLICABLE`.

### 4.4 Evidence Sufficiency Levels (3)
`STRONG`, `MODERATE`, `WEAK`.

### 4.5 Medical-vs-Trauma Causal Categories (3)
`TRAUMA_DOMINANT`, `MEDICAL_DOMINANT`, `MIXED_UNCLEAR`.

### 4.6 Structured Reason Codes (14)
All 14 project reason codes are preserved with full ontological parity:
1. `GRAVITATIONAL_EXPOSURE`
2. `MECHANICAL_ENTANGLEMENT`
3. `ELECTRICAL_CONTACT`
4. `PRESSURE_RELEASE`
5. `FIRE_EXPLOSION`
6. `CONFINED_SPACE`
7. `CHEMICAL_TOXIC_RELEASE`
8. `VEHICLE_COLLISION_LINE_OF_FIRE`
9. `NATURAL_MEDICAL_EVENT`
10. `LOW_ENERGY_SAME_LEVEL_FALL`
11. `LOW_ENERGY_MANUAL_TOOL`
12. `LOW_ENERGY_OFFICE_EQUIPMENT` *(Formally verified in summary, schema, and decision logic)*
13. `ROUTINE_NON_HAZARDOUS`
14. `INSUFFICIENT_INFORMATION`

---

## 5. Formal Decision Framework & Truth Table (18 Scenarios)

| ID | Scenario Description | Energy / Mechanism | Human Exposure | Barrier State | Consequence Potential | Evidence Sufficiency | Outcome Context | Final Label | Reason Code | Explanation & Precedence |
|---|---|---|---|---|---|---|---|---|---|---|
| **SC-01** | High energy + direct exposure + strong evidence | `GRAVITATIONAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | `STRONG` | Fracture / Hospitalized | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Fall from roof 18ft; energy and direct exposure confirm SIF regardless of barrier mention. |
| **SC-02** | High energy + exposure unknown | `ELECTRICAL` | `UNKNOWN` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | `WEAK` | None stated | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | 4,160V line arced in substation, but worker positioning and line-of-fire unstated. |
| **SC-03** | High energy + explicitly no exposure | `PRESSURE` | `NONE` | `NOT_APPLICABLE` | `NONE` | `STRONG` | None | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Pressure line ruptured inside isolated unmanned bunker; worker was in remote control room. |
| **SC-04** | High energy + successful barrier | `GRAVITATIONAL` | `POTENTIAL` | `SUCCESSFULLY_INTERVENED` | `FATAL_OR_LIFE_ALTERING` | `STRONG` | No injury | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Harness arrested 20ft fall from beam; SIF precursor with functioning barrier. |
| **SC-05** | Low energy slip + severe injury | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | `STRONG` | Fractured hip / Surgery | **`NO`** | `LOW_ENERGY_SAME_LEVEL_FALL` | Slipped on ice on flat ground; outcome decoupling overrides surgery/fracture. |
| **SC-06** | Manual tool + secondary high fall | `GRAVITATIONAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | `STRONG` | Broken ribs / Punctured lung | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Multi-mechanism: Wrench slipped (Tier 3) causing 2-level stair fall (Tier 1). Tier 1 controls. |
| **SC-07** | Medical event + workplace impact | `VEHICLE` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | `MODERATE` | Struck by forklift, died of cardiac arrest | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | Mixed/unclear causality between forklift trauma and fatal cardiac arrest at home. |
| **SC-08** | Injury-only narrative | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `INDETERMINATE` | `WEAK` | Injured hand during shift | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | Zero operational mechanism or hazard details; weak evidence enforces UNCERTAIN. |
| **SC-09** | Generic machine mention | `UNKNOWN` | `DIRECT` | `UNKNOWN` | `INDETERMINATE` | `WEAK` | Caught finger in machine | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | Machine type, power, and nip kinematics unstated; lacks physical proof. |
| **SC-10** | Electrical mention without contact | `ELECTRICAL` | `NONE` | `UNKNOWN` | `NONE` | `MODERATE` | No injury | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Worker was inspecting exterior of locked transformer enclosure; no contact or arc flash. |
| **SC-11** | Gas mention without toxic hazard | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | `STRONG` | Mild odor / No injury | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Sewer gas odor detected in parking lot; gas testing confirmed 0 ppm H2S. |
| **SC-12** | Fire mention without exposure | `FIRE_EXPLOSION` | `NONE` | `SUCCESSFULLY_INTERVENED` | `FATAL_OR_LIFE_ALTERING` | `STRONG` | None | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Deluge extinguished flash fire in automated spray booth; no workers present. |
| **SC-13** | Confined space with toxic gas | `CONFINED_SPACE` | `DIRECT` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | `STRONG` | Unconscious / Rescued | **`YES`** | `CONFINED_SPACE` | Entered sewer manhole without atmospheric testing or respirator; overcome by fumes. |
| **SC-14** | Negated exposure | `ELECTRICAL` | `NONE` | `NOT_APPLICABLE` | `NONE` | `STRONG` | No shock | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Breaker tripped; worker confirmed did not contact energized equipment. |
| **SC-15** | Multiple mechanism: caught in conveyor while clearing jam with stick | `MECHANICAL` | `DIRECT` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | `STRONG` | Amputation of arm | **`YES`** | `MECHANICAL_ENTANGLEMENT` | Manual stick use (Tier 3) coexists with powered conveyor nip (Tier 1). Tier 1 controls. |
| **SC-16** | Sparse narrative (<15 words) | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `INDETERMINATE` | `WEAK` | Worker hurt back lifting | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | Extreme brevity; insufficient facts to establish physical hazard energy. |
| **SC-17** | Office equipment incident | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | `STRONG` | Laceration / Stitches | **`NO`** | `LOW_ENERGY_OFFICE_EQUIPMENT` | Paper cutter blade grazed finger in administrative office; non-SIF mechanism. |
| **SC-18** | Potential exposure near-miss | `GRAVITATIONAL` | `POTENTIAL` | `FAILED` | `FATAL_OR_LIFE_ALTERING` | `STRONG` | Narrowly missed / No harm | **`YES`** | `GRAVITATIONAL_EXPOSURE` | 3,000-lb pipe fell from crane rigging, landing 3 feet from rigger; near-miss line-of-fire SIF. |

---

## 6. Output Schema Contract

The future V2.3 engine implementation will produce the following standardized schema:

```json
{
  "sif_label": "YES | NO | UNCERTAIN",
  "sif_precursor_type": "SIF_POTENTIAL_FAILED_OR_UNCONTROLLED | SIF_POTENTIAL_SUCCESSFUL_BARRIER | NO_SIF_POTENTIAL | UNCERTAIN",
  "controlling_hazard_energy": "GRAVITATIONAL | ELECTRICAL | MECHANICAL | PRESSURE | CHEMICAL | THERMAL | VEHICLE | FIRE_EXPLOSION | CONFINED_SPACE | NONE_LOW | UNKNOWN",
  "precedence_tier": "TIER_1_CATASTROPHIC | TIER_2_INTERMEDIATE | TIER_3_LOW_ENERGY | UNKNOWN",
  "human_exposure": "DIRECT | POTENTIAL | NONE | UNKNOWN",
  "barrier_state": "FAILED | SUCCESSFULLY_INTERVENED | ABSENT | PRESENT_NOT_ACTIVATED | UNKNOWN | NOT_APPLICABLE",
  "evidence_sufficiency": "STRONG | MODERATE | WEAK",
  "causal_nature": "TRAUMA_DOMINANT | MEDICAL_DOMINANT | MIXED_UNCLEAR",
  "potential_consequence": "FATAL_OR_PERMANENT_LIFE_ALTERING | TEMPORARY_MINOR_INJURY | INDETERMINATE",
  "reason_code": "One of 14 Approved Reason Codes",
  "evidence_text": "Verbatim substring from narrative (MANDATORY for YES/NO)",
  "confidence": "HIGH | MEDIUM | LOW",
  "outcome_context_quarantined": {
    "outcome_terms_detected": ["hospitalized", "fracture"],
    "influence_on_label": "NONE (Quarantined)"
  }
}
```

---

## 7. Human Validation & ML Retraining Gate

1. **Human Validation Requirement:**
   * This V2.3 specification is an **engineering design contract**, not verified ground truth.
   * Formal ground truth can only be established by double-blind annotation by two qualified human safety professionals on the 146-record pilot workspace created in Phase 4A.
2. **Machine Learning Block:**
   * **Transformer retraining remains STRICTLY BLOCKED.**
   * No model training is permitted until human validation confirms ground-truth labels and a calibrated candidate dataset is generated.

