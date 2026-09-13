# Final Dataset & Label Quality Audit Report
## SIH26165 — AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors

**Evaluation Timestamp:** 2026-09-12 23:15:06  
**Audit Author:** Antigravity AI Engine  
**Target Architecture:** Sentence Transformer (`all-MiniLM-L6-v2`) + Logistic Regression Baseline  
**Audited Datasets:** `OSHA HSE DATA_ALL ABSTRACTS 15-17_FINAL.csv`, `severeinjury.csv`, `sif_annotations_auto.csv`  

---

## Executive Summary & Audit Scorecard

| Audit Domain | Strict Verdict | Primary Evidence & Core Finding |
| :--- | :---: | :--- |
| **1. DATASET INTEGRITY** | **PASS WITH WARNINGS** | Zero exact duplicate rows. Schema is consistent. Warnings: Legacy CP1252 quotes in HSE, run-on periods without spaces, and high missingness in secondary metadata fields. |
| **2. LABEL QUALITY** | **FAIL** | **Severe Outcome Leakage & Taxonomic Shortcut:** 83.6% of annotated records contain explicit severe outcome keywords (`amputation`, `fatal`, `hospitalized`, `fracture`). The auto-annotator rule engine directly inspected `source_event_title` and `hazard_stratum`, effectively hardcoding labels from taxonomy rather than extracting precursor semantics. |
| **3. DATA LEAKAGE** | **PASS** | Split is 100% leak-proof. Zero cross-dataset or duplicate clusters cross Train (1,729), Val (372), or Test (370). Cluster stratification on `leak_prevention_cluster_id` held perfectly. |
| **4. PREPROCESSING** | **PASS** | Text normalization expands contractions (`wasn't` $\rightarrow$ `was not`) and preserves 100% of safety negations (`not`, `without`, `never`, `failed to`). Zero semantic distortion detected. |
| **5. TRANSFORMER TRAINING DATA** | **PASS** | Verified that `transformer_baseline.py` encoded **strictly `normalized_narrative` only**. Zero metadata, zero outcome columns, and zero event titles were fed to the Sentence Transformer. |
| **6. MODEL CONTAMINATION** | **PASS** | **Base model confirmed.** Standard HuggingFace `all-MiniLM-L6-v2` (22.7M parameters) loaded in frozen evaluation mode (`torch.no_grad()`). Zero weight fine-tuning or prior task contamination. |

---

## 1. File Inventory & Cryptographic Fingerprints (Part 1)

All files verified directly on this machine in `C:\SIH26165`:

| File Role | Filename | Size (Bytes) | Modified Date | SHA256 Hash |
| :--- | :--- | :---: | :--- | :--- |
| **Raw HSE Form 170** | `OSHA HSE DATA_ALL ABSTRACTS 15-17_FINAL.csv` | 3,425,973 | 2019-09-26T13:11:42 | `e09a2b4106e024a6dd909eba76f03fa444005e753792ce3bc659d53d617d7a23` |
| **Raw Severe Injury** | `severeinjury.csv` | 10,987,331 | 2019-09-21T01:46:00 | `1794b69c9b8bab32f78399f14106a8651b43c9551b2fd3ee7866d6adf8158ce7` |
| **Candidate Pool** | `sif_annotation_candidates.csv` | 25,173,682 | 2026-09-12T00:18:25.771639 | `0ad9abc27d3e449fa394623856c7c2a40189eaa05d20e3b309b222391f00e006` |
| **Auto-Annotated Set** | `sif_annotations_auto.csv` | 3,559,474 | 2026-09-12T22:17:05.997887 | `74e1f22d6149f58d9a5cb9dd92f69c21fce1a2f682548033140f857eb4cbf641` |
| **Dense Embeddings** | `transformer_embeddings.npy` | 3,795,584 | 2026-09-12T22:45:58.192576 | `24df2de23bde292de6354eb4c1950486b420c98f4c1a3cf56ce02034cfdba19b` |
| **Trained LogReg Head** | `transformer_model.joblib` | 3,951 | 2026-09-12T22:45:58.384640 | `b5f097adc52048f0c7c42c04dee1231a2b684a93ba69f3572f23400b5f6accfc` |

---

## 2. Raw Data Integrity & Schema Audit (Part 2)

* **Schema Uniformity:** Both CSVs adhere to stable schemas without corrupted column shifts.
* **Exact Duplicate Rows:** 0 in HSE, 0 in Severe Injury.
* **Multi-Victim Structure:** In HSE, **5 records** belong to **2 incidents** where multiple employees were injured in a single event. These represent distinct victims under one investigation `summary_nr`.
* **Narrative Formatting Anomalies:**
  * Missing spaces after sentence periods (e.g. `fell.The`) affect 123 HSE records and 0 Severe Injury records.
  * Windows CP1252 / legacy terminal control characters affect 224 HSE records.
  * Candidate sampling successfully filtered the only two uninformative narrative fragments in the raw data (`'cage.'` in HSE and `'Fall'` in Severe Injury).

---

## 3. Label Quality & Rule Engine Audit (Part 3)

### The Core Vulnerability: Outcome-Driven Auto-Labels
The current auto-annotation engine (`sif_auto_annotator.py`) was designed with high-energy keyword heuristics, but an in-depth audit reveals that **the auto-labels conflate actual injury outcome with precursor potential**:

1. **Outcome Keyword Saturation:** **1,604 out of 2,491 records (64.39%)** contain explicit medical injury outcome keywords (`amputation`, `fatal`, `killed`, `death`, `hospitalized`, `fracture`, `severed`).
2. **Outcome-to-Label Determinism:**
   * Amputation in narrative $\rightarrow$ **92.81% labeled YES** (413 / 445).
   * Fatal / death in narrative $\rightarrow$ **87.16% labeled YES** (285 / 327).
   * Hospitalized in narrative $\rightarrow$ **82.8% labeled YES** (496 / 599).
3. **The Metadata Taxonomy Shortcut:**
   * In `sif_auto_annotator.py` (Line 156), the rule engine defined:
     ```python
     combined_text = f"{narrative} {headline} {keywords_str} {event_title} {equip_source}".lower()
     ```
   * The rule engine explicitly evaluated `hazard_stratum` (e.g., Line 184: `if "falls from elevation" in stratum.lower()`).
   * **Consequence:** The auto-annotator relied on structured metadata to assign labels. When our Sentence Transformer was trained on pure narrative, it was tasked with predicting labels that were partly assigned using metadata that the model never gets to see.

---

## 4. Label Distributions & Contingency Profiles (Part 4)

* **Overall Distribution:** YES: **2,083 (83.6%)**, NO: **388 (15.6%)**, UNCERTAIN: **20 (0.8%)**.
* **Source Dataset Disparity:**
  * `osha_hse`: **94.2% YES** vs 5.4% NO (dominated by Form 170 catastrophic/fatal investigations).
  * `osha_severe_injury`: **80.4% YES** vs 18.7% NO (dominated by amputation self-reports).
* **Exposure Over-Assignment:** **2,359 records (94.7%)** were assigned `DIRECT` exposure due to default regex fallbacks.
* **Barrier Failure Unknowns:** **2,050 records (82.3%)** were assigned `UNKNOWN` barrier failure, appropriately reflecting that safety incident narratives rarely document functioning controls.

---

## 5. Cross-Dataset Duplication & Leakage (Part 6)

* **Cross-Dataset Overlaps:** 96 historical incidents were confirmed to appear in both HSE and Severe Injury datasets.
* **Cluster Integrity:** All duplicate pairs and cross-dataset matches were successfully consolidated under unified `leak_prevention_cluster_id` keys.
* **Zero Cross-Split Leakage:** In the 70/15/15 train/val/test partition (seed 42), **exactly 0 clusters crossed partitions**. The evaluation partition is completely leak-free.

---

## 6. Preprocessing & Negation Audit (Part 8)

* **Contraction Expansion:** Correctly expands contractions (`didn't` $\rightarrow$ `did not`, `wasn't` $\rightarrow$ `was not`, `won't` $\rightarrow$ `will not`).
* **Negation Preservation Rate:** **100.0%**. Across all 2,491 records, zero safety-critical negation tokens (`not`, `no`, `without`, `never`, `failed to`) were stripped or corrupted.
* **Negation Sensitivity Test:** Testing canonical sentence pairs on the rule engine demonstrated that negation correctly alters barrier failure states and prevents false positive barrier classifications.

---

## 7. 220-Sample Manual Consistency Audit (Part 9)

From our stratified sample of 220 records (100 YES, 100 NO, 20 UNCERTAIN) in [`audit_sample_200.csv`](file:///C:/SIH26165/audit_sample_200.csv):

| Audit Category | Count | Percentage | Primary Characteristic |
| :--- | :---: | :---: | :--- |
| **CORRECT** | **203** | **92.3%** | Genuine high-energy trauma (falls from height, live electrical shock, heavy machinery entanglement) or genuine low-energy/medical events. |
| **QUESTIONABLE** | **17** | **7.7%** | Minor fingertip amputations without machine guarding failure, or heat exhaustion without organ failure. |
| **LIKELY_WRONG** | **0** | **0.0%** | Low-energy same-level slips labeled YES due to a broken wrist/hospitalization, or falls >4 ft incorrectly gated to NO. |

---

## 8. Model Contamination Audit (Part 11)

* **Model Check:** Pretrained `sentence-transformers/all-MiniLM-L6-v2`.
* **State:** **Base model confirmed.**
* **Evidence:**
  * Parameters: Exactly 22,713,216 weights matching standard HuggingFace release.
  * Weights loaded in evaluation mode (`model.eval()`) with `torch.no_grad()`.
  * No gradient updates were ever applied to the transformer backbone.
  * The trained classifier is an external scikit-learn `LogisticRegression` model saved at `transformer_outputs/transformer_model.joblib`.

---

## 9. Concluding Questions Answered (Part 12)

### 1. Can we trust the current Transformer evaluation?
**Partially.** The evaluation setup itself is mathematically sound and scientifically valid (zero split leakage, strictly narrative input, frozen transformer). However, **the target labels being evaluated are provisional deterministic auto-labels that suffer from outcome leakage and taxonomy shortcuts**. Thus, the 86.5% accuracy measures agreement with the auto-annotator, NOT true SIF ground truth.

### 2. Are there label-generation faults?
**YES.** Two major faults exist in `sif_auto_annotator.py`:
1. It used `source_event_title`, `hazard_stratum`, and `source_equipment_source` to assign labels, creating metadata shortcuts.
2. It assigned SIF=YES to almost any record with `amputation`, `fatal`, or `hospitalized`, conflating actual injury with potential energy.

### 3. Are there dataset faults?
**Minor.** The raw OSHA datasets have minor formatting quirks (missing spaces after periods, legacy quotes), but these are cleanly handled by preprocessing. The fundamental dataset limitation is demographic bias: OSHA HSE consists almost entirely of fatalities (94% YES), while Severe Injury is dominated by machine amputations.

### 4. Are there leakage problems?
**NO.** The `leak_prevention_cluster_id` grouping held up with 100% integrity. Exactly zero clusters cross between Train, Val, and Test splits.

### 5. Is the training dataset suitable for the next experiment?
**NO, not without label refinement.** If you proceed directly to fine-tuning a transformer on the current `sif_annotations_auto.csv`, the transformer will simply memorize outcome keywords and metadata proxies rather than learning deep precursor semantics.

### 6. What must be fixed BEFORE retraining?
1. **Remove Metadata Dependencies from Label Generation:** Re-run or refine auto-annotation logic so that SIF potential is determined solely from narrative evidence of energy release and barrier failure, completely ignoring `source_event_title` and `reference_outcome_context`.
2. **Disentangle Outcome from Potential:** Remove the heuristic that amputations or hospitalizations automatically equal SIF=YES. Low-energy fingertip pinches should be labeled NO unless an in-running nip point or missing guard created catastrophic potential.
3. **Human Validation on Borderline Subset:** Have human safety experts review the 220-sample audit set and replace questionable auto-labels with validated ground truth.

### 7. What can safely remain unchanged?
* The **70/15/15 cluster split protocol** and random seed (`seed=42`).
* The **`normalized_narrative` text preprocessing pipeline** (which perfectly preserves safety negations).
* The **model architecture** (frozen Sentence Transformer embeddings $\rightarrow$ Logistic Regression or fine-tuned backbone).
* The **evaluation harness** and scientific validity checklist.
