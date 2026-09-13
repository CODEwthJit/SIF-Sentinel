# Proposed V2.3 SIF Engine Behavioral Test Contract
**Document Path:** `tests/test_sif_engine_v23_spec_contract.md`  
**Specification Reference:** `SIF_LABEL_ENGINE_V2.3_SPEC.md`  
**Status:** PROPOSED TEST CONTRACT (NOT YET EXECUTABLE CODE)  
**Total Behavioral Test Cases:** 52  

---

## 1. Test Suite Architecture & Verification Protocol

This document defines the formal behavioral test contract for the future implementation of SIF Label Engine V2.3.
It establishes **52 comprehensive test cases** across eight mandatory safety reasoning families designed to prevent regressions and audit edge-case performance:

* **Family 1:** Multiple-Mechanism Precedence Cases (10 cases: `TC-MM-01` to `TC-MM-10`)
* **Family 2:** Barrier State & Evidence Sufficiency Cases (10 cases: `TC-BE-01` to `TC-BE-10`)
* **Family 3:** Medical-vs-Trauma Causal Distinction (5 cases: `TC-MT-01` to `TC-MT-05`)
* **Family 4:** Outcome Bias Decoupling & Resistance (5 cases: `TC-OB-01` to `TC-OB-05`)
* **Family 5:** Syntactic Variation & Equivalence Classes (5 cases: `TC-SV-01` to `TC-SV-05`)
* **Family 6:** Negation Scope & Polarity Inversions (5 cases: `TC-NEG-01` to `TC-NEG-05`)
* **Family 7:** Low-Energy False-Positive Rejection (6 cases: `TC-LE-01` to `TC-LE-06`)
* **Family 8:** Exposure Geometry & Line-of-Fire (6 cases: `TC-EXP-01` to `TC-EXP-06`)

> [!IMPORTANT]
> **Specification Contract Status**
> These tests are defined as a formal specification contract. They will be converted into executable pytest code during the future V2.3 implementation phase after human validation.

---

## 2. Family 1: Multiple-Mechanism Precedence Cases (10 Cases)

| Test ID | Input Incident Narrative | Expected Mechanism | Expected Exposure | Expected Barrier | Expected Consequence | Expected Label | Expected Reason Code | Engineering Rationale |
|---|---|---|---|---|---|---|---|---|
| **TC-MM-01** | *An employee was on a stepladder installing a sprinkler pipe in a stairwell. He was on the fourth rung of an 8 foot step ladder tightening a fitting when the wrench slipped causing him to fall over the railing to the lower level, then roll down the stairs, ending up two levels below his starting point. He was hospitalized with a concussion, five broken ribs and a punctured lung.* (`PILOT_075`) | `GRAVITATIONAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Wrench slip (Tier 3) triggered 2-level stairwell fall (Tier 1). Tier 1 gravitational hazard controls SIF classification. |
| **TC-MM-02** | *A contractor was nippling up a production tree. The employee was tightening the bull plug and the wrench slipped off causing the employee to lose balance and to fall approximately 5 feet to the ground.* (`PILOT_076`) | `GRAVITATIONAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Tool slip (Tier 3) initiated elevation fall (Tier 1). Gravitational fall overrides manual tool rule. |
| **TC-MM-03** | *An employee was using a utility knife to cut cardboard when a forklift backed into his workstation, pinning his leg against a steel column.* | `VEHICLE` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `VEHICLE_COLLISION_LINE_OF_FIRE` | Utility knife (Tier 3) coexists with forklift line-of-fire (Tier 1). Vehicle impact controls. |
| **TC-MM-04** | *A worker was using a wooden stick to clear a jam in a powered belt conveyor when the stick and his hand were drawn into the in-running nip point.* | `MECHANICAL` | `DIRECT` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `MECHANICAL_ENTANGLEMENT` | Clearing jam with manual stick (Tier 3) led to powered conveyor nip crush (Tier 1). Powered machinery controls. |
| **TC-MM-05** | *An employee was sweeping dust with a broom near an electrical panel when an arc flash erupted from a loose 480V breaker.* | `ELECTRICAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `ELECTRICAL_CONTACT` | Routine sweeping (Tier 3) coexists with 480V arc flash (Tier 1). Electrical contact controls. |
| **TC-MM-06** | *A mechanic was using an air wrench to unbolt a flange on a high-pressure hydraulic line when the pressurized hose ruptured, releasing high-pressure fluid.* | `PRESSURE` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `PRESSURE_RELEASE` | Air tool use (Tier 2/3) coexists with high-pressure fluid release (Tier 1). Pressure release controls. |
| **TC-MM-07** | *An employee tripped on a pallet on the ground and bumped his knee against a stationary, unpowered lathe.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_SAME_LEVEL_FALL` | Same-level trip (Tier 3) with stationary non-operational equipment. Remains Tier 3 low-energy event. |
| **TC-MM-08** | *A worker was climbing a scaffold ladder while carrying a hand hammer; the hammer dropped from his hand and fell 30 feet, striking a worker below.* | `GRAVITATIONAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Carrying hand tool (Tier 3) led to 30ft dropped object impact (Tier 1). Gravitational falling load controls. |
| **TC-MM-09** | *An operator was applying grease with a hand gun to an unguarded operating gear drive when his sleeve caught in the gear teeth.* | `MECHANICAL` | `DIRECT` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `MECHANICAL_ENTANGLEMENT` | Manual greasing (Tier 3) coexists with unguarded running gear teeth (Tier 1). Mechanical crush controls. |
| **TC-MM-10** | *An employee was walking on a catwalk when a chemical process valve ruptured nearby, releasing a cloud of anhydrous ammonia.* | `CHEMICAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `CHEMICAL_TOXIC_RELEASE` | Walking (Tier 3) coexists with toxic chemical release (Tier 1). Chemical release controls. |

---

## 3. Family 2: Barrier State & Evidence Sufficiency Cases (10 Cases)

| Test ID | Input Incident Narrative | Expected Mechanism | Expected Exposure | Expected Barrier | Expected Consequence | Expected Label | Expected Reason Code | Engineering Rationale |
|---|---|---|---|---|---|---|---|---|
| **TC-BE-01** | *An employee was ascending a ladder to go onto a roof for an estimate when the ladder shifted. The employee fell from the ladder to the ground, fracturing ribs.* (`PILOT_010`) | `GRAVITATIONAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Roof access ladder fall; high kinetic energy + direct exposure proves SIF despite barrier silence. |
| **TC-BE-02** | *A worker was erecting a scaffold in an elevator shaft. He fell through an unsecured section of railing and struck the elevator pit floor, dying from his injuries.* (`PILOT_056`) | `GRAVITATIONAL` | `DIRECT` | `FAILED` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Unsecured railing and fall down elevator shaft to pit floor; unambiguous SIF precursor. |
| **TC-BE-03** | *An employee on a scaffold breaking rebar lost balance and fell over the wall 13 feet to the ground.* (`PILOT_057`) | `GRAVITATIONAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | 13ft fall from scaffold; physical height proves SIF potential even if barrier mention is omitted. |
| **TC-BE-04** | *Worker fell 20 feet from an elevated steel girder, but his personal fall arrest system deployed as engineered, arresting the fall without injury.* | `GRAVITATIONAL` | `POTENTIAL` | `SUCCESSFULLY_INTERVENED` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Precursor Type B: Functioning barrier prevented harm in an active high-consequence fall hazard. |
| **TC-BE-05** | *Employee was operating an industrial press brake with the light curtain interlock defeated; his hand entered the die, resulting in severe crushing.* | `MECHANICAL` | `DIRECT` | `FAILED` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `MECHANICAL_ENTANGLEMENT` | Defeated barrier (`FAILED`) with direct exposure to industrial press die. |
| **TC-BE-06** | *A worker was provided with a fall harness and lanyard while on a roof, but failed to tie off to the anchor point; worker fell 15 feet.* | `GRAVITATIONAL` | `DIRECT` | `PRESENT_NOT_ACTIVATED` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Barrier present on site but unattached (`PRESENT_NOT_ACTIVATED`); SIF precursor confirmed. |
| **TC-BE-07** | *A pressurized testing line burst at 3,000 psi; steel fragments impacted the polycarbonate safety blast shield, deflecting all debris.* | `PRESSURE` | `POTENTIAL` | `SUCCESSFULLY_INTERVENED` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `PRESSURE_RELEASE` | High-pressure blast with successful engineered shield intervention; genuine SIF precursor. |
| **TC-BE-08** | *Employee was working in a chemical manufacturing facility when a small puddle of water was noticed on the floor.* | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `INDETERMINATE` | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | Weak evidence; lacks physical hazard, exposure, or barrier context. |
| **TC-BE-09** | *A technician was racking in a 4,160V circuit breaker when an arc flash occurred, burning his face.* | `ELECTRICAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `ELECTRICAL_CONTACT` | High-voltage arc flash during breaker operation; direct exposure proves SIF. |
| **TC-BE-10** | *Substance was released in process unit. Worker was treated.* | `CHEMICAL` | `UNKNOWN` | `UNKNOWN` | `INDETERMINATE` | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | Weak evidence; chemical identity, volume, concentration, and exposure geometry unstated. |

---

## 4. Family 3: Medical-vs-Trauma Causal Distinction (5 Cases)

| Test ID | Input Incident Narrative | Expected Mechanism | Expected Exposure | Expected Barrier | Expected Consequence | Expected Label | Expected Reason Code | Engineering Rationale |
|---|---|---|---|---|---|---|---|---|
| **TC-MT-01** | *An employee was struck by a forklift backing out of a truck, injuring his leg. The next morning at 5:30 am, the employee died at home from fluid in his lungs and a heart attack.* (`PILOT_084`) | `VEHICLE` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | `MIXED_UNCLEAR` causality: co-occurrence of vehicle impact and delayed fatal cardiac event. |
| **TC-MT-02** | *An employee sitting at his desk in an office suffered a massive myocardial infarction and collapsed to the floor.* | `NONE_LOW` | `NONE` | `NOT_APPLICABLE` | `NATURAL_MEDICAL_OUTCOME` | **`NO`** | `NATURAL_MEDICAL_EVENT` | `MEDICAL_DOMINANT`: spontaneous internal physiological event without workplace trauma. |
| **TC-MT-03** | *An employee had a seizure while standing on flat ground in a warehouse and fell to the floor, bruising his shoulder.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `NATURAL_MEDICAL_EVENT` | `MEDICAL_DOMINANT`: seizure induced flat-ground fall; lacks high gravitational potential. |
| **TC-MT-04** | *An employee suffered a heart attack while standing on an unguarded roof edge 25 feet high, causing him to fall to the ground.* | `GRAVITATIONAL` | `DIRECT` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | `TRAUMA_DOMINANT`: Medical event triggered a 25ft fall from elevation; physical fall is a SIF hazard. |
| **TC-MT-05** | *A worker felt dizzy in a pump house on a warm day, sat down on a bench, and was transported to the clinic for dehydration observation.* | `THERMAL` | `UNKNOWN` | `UNKNOWN` | `INDETERMINATE` | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | `MIXED_UNCLEAR`: heat stress vs dehydration ambiguity with non-consequential outcome. |

---

## 5. Family 4: Outcome Bias Decoupling & Resistance (5 Cases)

| Test ID | Input Incident Narrative | Expected Mechanism | Expected Exposure | Expected Barrier | Expected Consequence | Expected Label | Expected Reason Code | Engineering Rationale |
|---|---|---|---|---|---|---|---|---|
| **TC-OB-01** | *An employee slipped and fell on ice after washing oil from a pump on flat ground. The employee sustained a fractured ankle that required surgical reconstruction.* (`PILOT_004`) | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_SAME_LEVEL_FALL` | Same-level fall on ice; surgery and fracture do not convert low-energy slip into a SIF precursor. |
| **TC-OB-02** | *An administrative assistant was using a heavy-duty paper cutter and lacerated her thumb, requiring emergency room stitches and hospitalization.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_OFFICE_EQUIPMENT` | Office paper cutter; hospitalization does not convert administrative task into SIF. |
| **TC-OB-03** | *An employee was pushing a two-wheeled hand cart over a flat threshold when a wheel rolled over his toe, fracturing the big toe.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Non-powered hand cart on flat ground; localized toe fracture is not a SIF precursor. |
| **TC-OB-04** | *A worker was walking in a well-lit hallway, tripped over an uneven carpet seam, fell to the floor, and broke his collarbone.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_SAME_LEVEL_FALL` | Flat-ground trip on carpet seam; bone fracture does not override low kinetic energy. |
| **TC-OB-05** | *An employee was tightening a bolt with a hand wrench, slipped, and struck his elbow on a table, sustaining a hairline fracture.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_MANUAL_TOOL` | Manual hand tool slip; localized fracture does not establish SIF precursor capacity. |

---

## 6. Family 5: Syntactic Variation & Equivalence Classes (5 Cases)

| Test ID | Input Incident Narrative | Expected Mechanism | Expected Exposure | Expected Barrier | Expected Consequence | Expected Label | Expected Reason Code | Engineering Rationale |
|---|---|---|---|---|---|---|---|---|
| **TC-SV-01** | *Worker plunged from an elevated platform through an unsecured catwalk opening, falling 16 feet to the concrete slab.* | `GRAVITATIONAL` | `DIRECT` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Equivalence Class A: 'plunged from platform through opening' matches elevation fall. |
| **TC-SV-02** | *An operator's sleeve was drawn into the in-running rollers of a high-speed laminating press, compressing his arm.* | `MECHANICAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `MECHANICAL_ENTANGLEMENT` | Equivalence Class B: 'drawn into in-running rollers compressing arm' matches mechanical crush. |
| **TC-SV-03** | *A rigger was pinned against a concrete barrier by a reversing front-end loader that backed over the work area.* | `VEHICLE` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `VEHICLE_COLLISION_LINE_OF_FIRE` | Equivalence Class C: 'pinned against barrier by reversing loader' matches vehicle line-of-fire. |
| **TC-SV-04** | *Employee descended unintentionally from roof eave when decking gave way, dropping to lower level 12 feet below.* | `GRAVITATIONAL` | `DIRECT` | `FAILED` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Equivalence Class A: 'descended unintentionally from roof eave' matches elevation fall. |
| **TC-SV-05** | *Maintenance tech contacted live industrial distribution busbar inside 480V motor control center.* | `ELECTRICAL` | `DIRECT` | `UNKNOWN` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `ELECTRICAL_CONTACT` | Equivalence Class: 'contacted live distribution busbar in 480V MCC' matches electrical contact. |

---

## 7. Family 6: Negation Scope & Polarity Inversions (5 Cases)

| Test ID | Input Incident Narrative | Expected Mechanism | Expected Exposure | Expected Barrier | Expected Consequence | Expected Label | Expected Reason Code | Engineering Rationale |
|---|---|---|---|---|---|---|---|---|
| **TC-NEG-01** | *A 480V circuit breaker experienced a flashover, but the technician was outside the arc flash boundary and did not contact energized conductors.* | `ELECTRICAL` | `NONE` | `NOT_APPLICABLE` | `NONE` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Negated exposure: 'did not contact energized conductors' + outside boundary. |
| **TC-NEG-02** | *A worker entered a permit-required sewer vault without wearing a supplied-air respirator or performing atmospheric testing.* | `CONFINED_SPACE` | `DIRECT` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `CONFINED_SPACE` | Negated barrier: 'without wearing respirator' confirms absent barrier in toxic space. |
| **TC-NEG-03** | *An employee fell off an extension ladder, but was not wearing a fall harness and landed 14 feet below.* | `GRAVITATIONAL` | `DIRECT` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Negated barrier: 'was not wearing fall harness' confirms absent fall protection. |
| **TC-NEG-04** | *Interlock was inspected and guard was not removed; worker operated press safely with zero hazard contact.* | `MECHANICAL` | `NONE` | `SUCCESSFULLY_INTERVENED` | `NONE` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Double negation/safeguard: 'guard was not removed' confirms active physical protection. |
| **TC-NEG-05** | *High pressure line ruptured, but the area had been cleared and no employees were exposed to the blast.* | `PRESSURE` | `NONE` | `NOT_APPLICABLE` | `NONE` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Negated exposure: 'no employees were exposed' establishes absence of human exposure. |

---

## 8. Family 7: Low-Energy False-Positive Rejection (6 Cases)

| Test ID | Input Incident Narrative | Expected Mechanism | Expected Exposure | Expected Barrier | Expected Consequence | Expected Label | Expected Reason Code | Engineering Rationale |
|---|---|---|---|---|---|---|---|---|
| **TC-LE-01** | *Employee was closing a metal file cabinet drawer and bumped her index finger, suffering a bruised nail.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_OFFICE_EQUIPMENT` | Routine administrative office task; low kinetic energy. |
| **TC-LE-02** | *Worker was stapling documents with an electric desk stapler and accidentally punctured skin with a staple.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_OFFICE_EQUIPMENT` | Office electric stapler; superficial puncture lacks SIF capacity. |
| **TC-LE-03** | *An employee was walking across an office carpet and stumbled on his own shoelace, falling to his knees.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_SAME_LEVEL_FALL` | Flat-ground stumble; zero elevation hazard. |
| **TC-LE-04** | *Worker was tightening a small screw on a computer monitor with a manual jeweler's screwdriver when it slipped, scratching his finger.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `LOW_ENERGY_MANUAL_TOOL` | Precision manual screwdriver; minor superficial scratch. |
| **TC-LE-05** | *Employee opened an exterior door on a windy day; the door swung back and bumped his shoulder.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Routine non-hazardous building ingress/egress. |
| **TC-LE-06** | *A clerk was carrying a ream of printer paper down the hallway and felt a minor muscle twitch in his forearm.* | `NONE_LOW` | `DIRECT` | `NOT_APPLICABLE` | `MINOR_OR_LOCALIZED` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Routine non-hazardous manual handling. |

---

## 9. Family 8: Exposure Geometry & Line-of-Fire (6 Cases)

| Test ID | Input Incident Narrative | Expected Mechanism | Expected Exposure | Expected Barrier | Expected Consequence | Expected Label | Expected Reason Code | Engineering Rationale |
|---|---|---|---|---|---|---|---|---|
| **TC-EXP-01** | *A 4,000-lb bundle of steel beams fell from an overhead crane rigging, crashing directly into an occupied pedestrian walkway 5 feet from two workers.* | `GRAVITATIONAL` | `POTENTIAL` | `FAILED` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `GRAVITATIONAL_EXPOSURE` | Near-miss line-of-fire: massive suspended falling load landed in immediate proximity. |
| **TC-EXP-02** | *A crane dropped a concrete bucket into an excluded, barricaded drop zone where zero personnel were permitted or present.* | `GRAVITATIONAL` | `NONE` | `SUCCESSFULLY_INTERVENED` | `NONE` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Excluded barricaded zone; total absence of human exposure converts to non-SIF. |
| **TC-EXP-03** | *A forklift carrying pallets turned a corner and grazed an empty pallet rack; workers were in another aisle 50 feet away.* | `VEHICLE` | `NONE` | `NOT_APPLICABLE` | `NONE` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Forklift collision occurred far outside any worker line-of-fire. |
| **TC-EXP-04** | *A worker was standing within the swing radius of an operating hydraulic excavator without a barricade when the counterweight swung past his head.* | `VEHICLE` | `POTENTIAL` | `ABSENT` | `FATAL_OR_LIFE_ALTERING` | **`YES`** | `VEHICLE_COLLISION_LINE_OF_FIRE` | Direct presence inside mobile equipment swing radius line-of-fire without barricade. |
| **TC-EXP-05** | *A high-pressure steam valve leaked inside a locked, automated boiler room; all operators were stationed in the remote digital control center.* | `THERMAL` | `NONE` | `SUCCESSFULLY_INTERVENED` | `NONE` | **`NO`** | `ROUTINE_NON_HAZARDOUS` | Remote isolation prevented human exposure to high-pressure thermal steam leak. |
| **TC-EXP-06** | *A pipe burst in an outdoor yard; narrative states worker was on site but does not specify distance or exposure.* | `PRESSURE` | `UNKNOWN` | `UNKNOWN` | `INDETERMINATE` | **`UNCERTAIN`** | `INSUFFICIENT_INFORMATION` | Ambiguous positioning; presence on site without line-of-fire detail forces UNCERTAIN. |

