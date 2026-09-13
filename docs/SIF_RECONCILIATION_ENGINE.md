# SIF Reconciliation Engine Specification & Integration Design

**Project**: SIH26165 — SIF Precursor Detection  
**Module**: `src/sif_reconciliation_engine.py` & `src/sif_pipeline.py`  
**Phase**: 7.2 (Final Reconciliation Architecture)  
**Status**: COMPLETE & FROZEN  

---

## 1. Purpose & Overview

The **SIF Reconciliation Engine** is the downstream integration component that unifies predictions from the frozen Machine Learning model (Phase 6.1 TF-IDF + Logistic Regression, $\tau = 0.59$) and the frozen deterministic domain rule engine (V2.3 Engine, `2.3.0-BUGFIX-FROZEN`) into an auditable, categorical triage assessment.

Rather than obscuring conflicts behind synthetic averaging formulas, the engine treats ML statistical propensity and rule-based energy reasoning as **independent evidence channels**. It surfaces consensus, uncertainty, and domain disagreements transparently, establishing clear operational triage priorities for human safety professionals.

---

## 2. End-to-End System Architecture

The pipeline processes unstructured incident text through decoupled, quarantined stages:

```
                  ┌───────────────────────────────┐
                  │    Raw Incident Narrative     │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │      NLP Preprocessing        │
                  │ (Whitespace / Text Clean-up)  │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
     ┌────────────────────────┐      ┌────────────────────────┐
     │  Frozen ML Predictor   │      │ Frozen Rule Engine V2.3│
     │   (Phase 6.1 TF-IDF)   │      │   (Precedence Tiers)   │
     │  Threshold tau = 0.59  │      │   Energy Mechanisms    │
     └────────────┬───────────┘      └────────────┬───────────┘
                  │                               │
                  │ ml_label, ml_score            │ sif_label, energy,
                  │ lexical evidence              │ reason_code, barrier
                  │                               │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │   SIF Reconciliation Engine   │
                  │  Categorical Triage Matrix    │
                  │  Discrepancy & Gating Logic   │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │   Structured Auditable Result │
                  │  (Status, Priority, Rationale)│
                  └───────────────────────────────┘
```

### Module Decoupling & Component Roles

| Component | File Path | Function / Role |
| :--- | :--- | :--- |
| **ML Inference** | `ml/sif_ml_predictor.py` | `SIFMLPredictor.predict()`: Pure narrative inference using locked vocabulary and regression weights ($C=100.0, \tau=0.59$). Returns statistical propensity and lexical feature contributions. |
| **Rule Reasoning** | `src/sif_auto_annotator_v23.py` | `SIFAutoAnnotatorV23.annotate_narrative()`: Narrative-only deterministic classification evaluating energy release, barrier state, and exposure precedence. |
| **Reconciliation** | `src/sif_reconciliation_engine.py` | `SIFReconciliationEngine.reconcile()`: Pure categorical agreement matrix. Evaluates consensus vs disagreement without numerical weighting. |
| **Pipeline Service** | `src/sif_pipeline.py` | `analyze_report()`: Public orchestrator running end-to-end normalization, parallel inference, reconciliation, and output assembly. |

---

## 3. Categorical Agreement Matrix

The engine maps all combinations of ML and Rule outputs to exactly five discrete states:

| ML Prediction | Rule Label (V2.3) | Reconciliation Status | Operational Review Priority | Discrepancy Flag | Human Review Required |
| :---: | :---: | :--- | :---: | :---: | :---: |
| **YES** ($\ge 0.59$) | **YES** | `CONSENSUS_SIF` | **HIGH** | `False` | `False` |
| **NO** ($< 0.59$) | **NO** | `CONSENSUS_NON_SIF` | **LOW** | `False` | `False` |
| **YES** ($\ge 0.59$) | **UNCERTAIN** | `RULE_UNCERTAIN_ML_SIGNAL` | **HIGH** | `True` | `True` |
| **NO** ($< 0.59$) | **UNCERTAIN** | `RULE_UNCERTAIN_NO_ML_SIGNAL` | **MEDIUM** | `True` | `True` |
| **YES** ($\ge 0.59$) | **NO** | `DIRECT_DISAGREEMENT` | **HIGH** | `True` | `True` |
| **NO** ($< 0.59$) | **YES** | `DIRECT_DISAGREEMENT` | **HIGH** | `True` | `True` |

---

## 4. Why No Weighted Formula is Used

> [!IMPORTANT]
> The reconciliation engine strictly prohibits continuous mathematical blending (e.g., `final_score = x * ML + y * Rule`).

### Scientific & Operational Rationale:
1. **Incompatible Semantics**:
   - The ML score ($\text{ml\_score} \in [0.0, 1.0]$) represents a **statistical likelihood** of class membership under the provisional automated V2.3 labeling rules. It is **NOT** a physical probability of death or injury.
   - The Rule output represents a **symbolic deduction** based on physical energy forms (gravitational, electrical, mechanical, pressure).
   - Averaging a statistical log-odds propensity with a discrete symbolic state produces a meaningless hybrid number that corrupts both frameworks.
2. **Obscuring Safety Disagreements**:
   - In safety-critical systems, disagreements between independent detection mechanisms represent valuable operational information.
   - For example, if ML outputs $0.80$ (due to words like "pressurized line") but the rule engine outputs `NO` (because the narrative states the line was tagged out and zero-energy was confirmed), an averaged score of $0.55$ falsely suggests a borderline event.
   - In reality, this is a **Domain Disagreement** that must be surfaced directly to safety auditors rather than suppressed.
3. **Audit Trail Integrity**:
   - Safety regulators and incident investigation teams require clear causal rationales: *Why was this classified as a precursor?*
   - Categorical matrix outputs preserve full traceability: ML lexical tokens and Rule energy mechanisms remain accessible and uncorrupted.

---

## 5. Discrepancy Handling & Human Review Gating

The reconciliation engine functions as an operational **triage gateway**:

- **Consensus States (`discrepancy_flag = False`, `review_required = False`)**:
  - `CONSENSUS_SIF`: Routed directly to senior EHS investigators for formal high-potential corrective action tracking.
  - `CONSENSUS_NON_SIF`: Routed to routine safety recordkeeping with minimal administrative overhead.
- **Discrepancy & Uncertainty States (`discrepancy_flag = True`, `review_required = True`)**:
  - `RULE_UNCERTAIN_ML_SIGNAL`: Indicates narratives where statistical precursor language is strong, but specific syntactic proof (e.g., exact fall height or voltage level) is missing. Flagged as **HIGH** priority for rapid investigator clarification.
  - `DIRECT_DISAGREEMENT`: Indicates sharp divergence between lexical statistics and deterministic rules. Gated as **HIGH** priority audit cases.
  - `RULE_UNCERTAIN_NO_ML_SIGNAL`: Indicates routine narratives with insufficient detail. Assigned **MEDIUM** priority triage.

---

## 6. Strict Runtime Metadata Quarantine

To eliminate outcome bias, hindsight bias, and data leakage, the entire pipeline enforces a strict metadata quarantine:

- **Prohibited Keys**:
  `hospitalized`, `amputation`, `fatal`, `source_event_code`, `source_event_title`, `source_nature_title`, `source_part_title`, `source_equipment_source`, `reference_outcome_context`, `candidate_stratum`, `sampling_batch`.
- **Runtime Assertion**:
  Attempting to pass any prohibited key in the input narrative dictionary, the ML payload, or the Rule payload immediately raises a `ValueError` (`Metadata quarantine violation`), aborting execution.

---

## 7. Limitations

1. **Narrative Dependency**:
   - Both the ML model and rule engine operate solely on textual descriptions. If an incident report omits critical facts (e.g., fall height or electrical voltage), the rule engine correctly defaults to `UNCERTAIN`.
2. **Vocabulary Overlap**:
   - Benign industrial operations using words commonly associated with high hazards (e.g., "crane inspection", "high voltage substation walkthrough") may produce elevated ML scores, leading to `RULE_UNCERTAIN_ML_SIGNAL` or `DIRECT_DISAGREEMENT`.
3. **Non-Probabilistic Output**:
   - Output scores must never be interpreted as actuarial accident probabilities.

---

## 8. Mandatory Scientific Disclaimer

> [!WARNING]
> **Scientific Disclaimer**  
> "The reconciliation result is an engineering triage output derived from a provisional automated rule framework and an ML model trained against those provisional labels. It is not independently validated SIF ground truth."

This system is an automated triage decision-support tool designed to assist qualified safety professionals. It must **not** be used as an autonomous safety decision maker without qualified human review.

