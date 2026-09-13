# Machine Learning Integration Contract
**Project**: SIH26165 — AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors  
**Document Version**: `1.0.0-PHASE7.1`  
**Target Architecture**: Hybrid Multi-Stage SIF Risk Engine  

---

## 1. System Context & Architectural Flow

The SIF Precursor Detection System operates across four decoupled architectural stages:

```
[Raw Incident Record]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 1. NLP Preprocessing Layer                             │
│    • Contraction expansion                             │
│    • Whitespace normalization                          │
│    • Strict metadata isolation                         │
└────────────────────────────────────────────────────────┘
         │
         ├─── normalized_narrative
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 2. ML Predictor (sih26165_sif_ml_predictor)            │
│    • TF-IDF feature extraction (4,886 n-grams)         │
│    • Logistic Regression inference (tau = 0.59)        │
│    • Feature-level evidence attribution (w_j * x_j)   │
└────────────────────────────────────────────────────────┘
         │
         ├─── ml_label, ml_score, threshold, lexical_evidence
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 3. Deterministic SIF Rule Engine (V2.3 Frozen)         │
│    • Symbolic hazard energy detection                  │
│    • Barrier state evaluation                          │
│    • Precedence tier resolution                        │
│    • Controlled reason coding                          │
└────────────────────────────────────────────────────────┘
         │
         ├─── sif_label_v23, reason_code_v23, hazard_energy_v23, barrier_state_v23
         │
         ▼
┌────────────────────────────────────────────────────────┐
│ 4. SIF Risk Assessment & Reconciliation Engine         │
│    • Structural evidence aggregation                   │
│    • Discrepancy flagging (ML vs. Rule divergence)     │
│    • Human-in-the-loop review gating                   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Component Interface Specifications

### Stage 1: NLP Preprocessing Layer $\rightarrow$ ML Predictor
* **Transport**: In-memory string or dictionary.
* **Payload**:
  ```python
  "normalized_narrative": str  # Non-empty, sanitized text
  ```
* **Quarantine Enforcement**: The ML interface **strictly rejects** any payload containing metadata keys (such as `hospitalized`, `amputation`, `source_event_code`, `hazard_energy`, or outcomes). Attempting to pass non-narrative columns raises an immediate `ValueError`.

---

### Stage 2: ML Predictor Output Specification
* **Module**: `ml.sif_ml_predictor.SIFMLPredictor`
* **Method**: `predict(input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]`
* **Output Schema**:
  ```json
  {
    "ml_label": "YES" | "NO",
    "ml_score": 0.8950,
    "threshold": 0.59,
    "positive_evidence": [
      {
        "feature": "falling feet",
        "contribution": 0.7231,
        "tfidf_value": 0.1321,
        "weight": 5.4759
      }
    ],
    "negative_evidence": [
      {
        "feature": "heart attack",
        "contribution": -1.8973,
        "tfidf_value": 0.2601,
        "weight": -7.2952
      }
    ],
    "decision_rationale": "Score 0.8950 >= threshold 0.59. Dominant SIF evidence: 'falling feet' (+0.72)."
  }
  ```

* **Contractual Properties**:
  * `ml_score`: Guaranteed float strictly bounded in $[0.0, 1.0]$.
  * `threshold`: Locked float constant ($0.59$).
  * `ml_label`: Strictly derived via deterministic thresholding:
    $$\text{ml\_label} = \begin{cases} \text{"YES"} & \text{if } \text{ml\_score} \ge 0.59 \\ \text{"NO"} & \text{if } \text{ml\_score} < 0.59 \end{cases}$$
  * `positive_evidence` / `negative_evidence`: Contains **only** n-grams that explicitly appear in the input narrative with non-zero TF-IDF weight.

---

### Stage 3: Deterministic Rule Engine Input / Output
* **Module**: `src.sif_auto_annotator_v23.SIFAutoAnnotatorV23`
* **Input**: `{"normalized_narrative": str}`
* **Output**:
  ```json
  {
    "sif_label": "YES" | "NO" | "UNCERTAIN",
    "sif_precursor_type": "SIF_POTENTIAL_FAILED_OR_UNCONTROLLED" | "NO_SIF_POTENTIAL" | "UNCERTAIN",
    "controlling_hazard_energy": "GRAVITATIONAL" | "ELECTRICAL" | ...,
    "barrier_state": "FAILED" | "ABSENT" | "UNKNOWN" | "NOT_APPLICABLE",
    "reason_code": "GRAVITATIONAL_EXPOSURE" | "INSUFFICIENT_INFORMATION" | ...
  }
  ```

---

### Stage 4: Downstream SIF Risk Engine Contract
* **Input Aggregate**:
  ```python
  {
      "narrative": str,
      "ml_result": {
          "label": str,       # "YES" or "NO"
          "score": float,     # e.g. 0.925
          "evidence": list    # Contributing tokens
      },
      "rule_result": {
          "label": str,       # "YES", "NO", or "UNCERTAIN"
          "reason_code": str, # e.g. "GRAVITATIONAL_EXPOSURE"
          "energy": str,      # e.g. "GRAVITATIONAL"
          "barrier": str      # e.g. "ABSENT"
      }
  }
  ```

---

## 3. Strict Semantic Definition of `ml_score`

To prevent dangerous misinterpretations by downstream consumers, the following mathematical definition is contractually locked:

> [!CAUTION]
> ### What `ml_score` IS NOT:
> * **NOT** a physical probability of death.
> * **NOT** a probability of hospitalization or severe injury.
> * **NOT** an official OSHA / HSE inspection risk score.
> * **NOT** an autonomous substitute for safety-engineering hazard assessments.
> 
> ### What `ml_score` IS:
> * The **model-estimated statistical likelihood of belonging to the `YES` class under the provisional V2.3 automated annotation framework**.

---

## 4. Gating & Discrepancy Reconciliation Principles

1. **Zero Magic Formulas**:  
   Downstream systems must **NOT** combine the ML score and rule engine outputs through arbitrary weighted arithmetic (e.g. `final_score = 0.7 * ML + 0.3 * Rules`). Such formulas lack physical grounding and mask safety-critical disagreements.

2. **Categorical Agreement Matrix**:
   * **Consensus SIF** (`ML == YES` and `Rules == YES`): High confidence SIF precursor. Auto-routed to priority mitigation queues.
   * **Consensus Non-SIF** (`ML == NO` and `Rules == NO`): High confidence non-SIF incident (e.g. natural medical event, low-energy office mishap).
   * **Rule Uncertainty with Strong ML Signal** (`Rules == UNCERTAIN` and `ML == YES` with high score): Narrative contains rich statistical markers of high energy, but lacks explicit syntactic evidence for rule firing. **Flagged for human safety review**.
   * **Direct Disagreement** (`Rules == YES` and `ML == NO`, or `Rules == NO` and `ML == YES`): Signals a potential domain edge-case (e.g., manual wrench near conveyor, or metric dilution). **Must trigger an adversarial discrepancy audit, never an automated compromise**.

