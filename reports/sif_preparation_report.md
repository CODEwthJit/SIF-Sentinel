# SIF Precursor Annotation Data Preparation Report

**Date:** September 2026  
**Pipeline Author:** Antigravity AI  
**Target Goal:** Prepare unified, clean, leak-proof candidate records from OSHA HSE and Severe Injury datasets for Significant Injury and Fatality (SIF) precursor annotation.

---

## 1. Compliance & Constraint Verification

In accordance with strict project instructions:
* [x] **No ML Model Training:** No machine learning, neural, or statistical models were trained.
* [x] **No Synthetic Data Generation:** Zero synthetic narratives or synthetic records were generated.
* [x] **No Automatic SIF Label Assignment:** Ground-truth SIF labels were **not** assigned automatically from `Fatal`, `Hospitalized`, `Amputation`, `Event`, or any other outcome field. Observed severity indicators are strictly sequestered into `reference_outcome_context` for human/framework evaluation.
* [x] **Source Integrity Preserved:** Original CSV files remained completely untouched. All unified records preserve their `source_dataset`, `source_record_id`, and `source_secondary_id`.
* [x] **Negation Semantics Preserved:** Safety-critical negation words (e.g., *not, no, never, without, failed to, neither, nor, lack of, inoperable*) and safety prefixes (*unprotected, unsecured, unguarded*) were rigorously protected during text normalization.

---

## 2. Ingestion & Profile of Unified Pipeline

| Metric | OSHA HSE Abstracts | OSHA Severe Injury Reports | Unified Candidate Base |
| :--- | :--- | :--- | :--- |
| **Source File** | `OSHA HSE DATA_ALL ABSTRACTS 15-17_FINAL.csv` | `severeinjury.csv` | [`sif_annotation_candidates.csv`](file:///c:/SIH26165/sif_annotation_candidates.csv) |
| **Raw Records Ingested** | 4,847 | 21,578 | 26,425 |
| **Primary Narrative Field** | `Abstract Text` | `Final Narrative` | `normalized_narrative` (with `original_narrative` preserved) |
| **Invalid Records Removed** | 1 (0.02%) | 1 (<0.01%) | 2 records (<0.01%) |
| **Valid Candidate Records** | **4,846** | **21,577** | **26,423** |
| **Primary Identifier** | `summary_nr` (OSHA Form 170) | `UPA` (Unprogrammed Activity) | `candidate_id` (`HSE_{summary_nr}_{idx}` / `SIR_{UPA}`) |
| **Secondary Identifier** | Form 170 Case ID | `ID` (SIR sequence number) | `source_secondary_id` |
| **Leak-Prevention Clusters** | — | — | **26,269** discrete clusters |

---

## 3. Invalid Narrative Profiling & Filtering

Narratives were profiled to identify corrupted text fragments and uninformative placeholders that provide insufficient context for human or automated SIF-precursor evaluation.

### Removed Records Log
| Source Dataset | Record ID | Original Text | Length | Reason for Removal |
| :--- | :--- | :--- | :---: | :--- |
| `osha_hse` | `summary_nr 220873897` | `'cage.'` | 5 chars / 1 word | Fragmented line artifact from multi-line CSV split. |
| `osha_severe_injury` | `UPA 981824` (ID 2015052519) | `'Fall'` | 4 chars / 1 word | Single-word placeholder lacking any event or precursor detail. |

All remaining **26,423** records contain substantive narrative descriptions (mean length: 228.3 characters; median: 177.0 characters; up to 3,291 characters).

---

## 4. Safety-Preserving Text Normalization

Standard natural language preprocessing (such as aggressive lowercasing, stop-word removal, or regex stripping) often destroys vital safety negation (e.g., converting *"worker was not wearing fall protection"* into *"worker wearing fall protection"*). 

### Normalization Rules Implemented:
1. **Negation Expansion & Protection:** Contractions are systematically expanded into explicit negation forms:
   * `wasn't` $\rightarrow$ `was not`
   * `didn't` $\rightarrow$ `did not`
   * `couldn't` $\rightarrow$ `could not`
   * `wouldn't` $\rightarrow$ `would not`
   * `shouldn't` $\rightarrow$ `should not`
   * `can't` $\rightarrow$ `cannot`
   * `won't` $\rightarrow$ `will not`
   * `isn't` / `aren't` $\rightarrow$ `is not` / `are not`
   * `haven't` / `hasn't` $\rightarrow$ `have not` / `has not`
2. **Encoding Artifact Cleansing:**
   * Resolved 7-bit masked ASCII control characters common in legacy OSHA Form 170 text (`\x18` and `\x19` converted to single quotes `'`; `\x1c`, `\x1d`, and `\x13` converted to standard double quotes `"`).
   * Resolved Windows-1252 / CP1252 smart quotes (`\x91`, `\x92`, `\x93`, `\x94`, `’`, `‘`, `“`, `”`) to standard ASCII quotes.
   * Standardized em-dashes and en-dashes (`–`, `—`, `\x96`, `\x97`) to hyphens `-`.
   * Replaced non-breaking spaces `\xa0` and control byte `\x03`.
3. **Whitespace Normalization:**
   * Consolidated line breaks, carriage returns, tabs, and duplicate spaces into single clean spaces while preserving casing, punctuation, and numerical measurements (e.g., `12.5 feet`, `480 volts`).

### Narrative Length Statistics: Raw vs. Normalized
| Field & Dataset | Metric | Raw Text | Normalized Text |
| :--- | :--- | :---: | :---: |
| **OSHA HSE `Abstract Text`** | Mean Length (Chars) | 412.44 | **412.40** |
| | Median Length (Chars) | 338.0 | **338.0** |
| | Mean Word Count | 71.82 | **71.88** (contractions expanded) |
| **OSHA Severe Injury `Final Narrative`** | Mean Length (Chars) | 187.01 | **186.99** |
| | Median Length (Chars) | 168.0 | **168.0** |
| | Mean Word Count | 32.48 | **32.52** |

---

## 5. Deduplication & Cross-Dataset Leak Prevention

To prevent data contamination and overly optimistic evaluation across future train/test partitions, duplicate and near-duplicate incidents were tracked and isolated in [`duplicate_flags.csv`](file:///c:/SIH26165/duplicate_flags.csv).

### 5.1 Deduplication Breakdown
* **Exact Normalized Text Duplicates:** **68 records** across 33 duplicate groups.
  * In HSE: 38 records (multi-victim incidents sharing investigation text).
  * In Severe Injury: 30 records (recurrent employer boilerplate text, e.g., *"An employee suffered a finger amputation."*).
* **Near-Duplicates on Same Date:** **50 records** (records on the same date with Jaccard token similarity $\ge 0.75$).

### 5.2 Cross-Dataset Semantic Incident Matches (96 Confirmed Pairs)
During audit analysis, 96 identical real-world incidents were confirmed to exist across both datasets (representing an employer severe injury self-report that escalated into a formal OSHA Form 170 inspection abstract).

* **Total Flagged Match Records:** **192 entries** (96 pairs).
* **High-Confidence Indicators:** Exact matching event date, matching employer/location, and text Jaccard similarity $\ge 0.30$.
* **Inspection Correlation:** In **91.7%** of these matches, the Severe Injury record contains a formal OSHA inspection number.

### 5.3 Leak-Prevention Graph Clustering
A graph connected-components algorithm was executed over all exact duplicates, near-duplicates, and cross-dataset matches:
* Generated **26,269 discrete clusters** (`leak_prevention_cluster_id`).
* Any two records that share physical incident details, identical wording, or cross-dataset overlap are assigned the **same cluster ID**.
* **Model Partitioning Rule:** When creating train/validation/test splits, partitions **must** be grouped by `leak_prevention_cluster_id`. No cluster should ever be partitioned across train and test.

---

## 6. Hazard & Energy Mechanism Stratification

Without assigning ground-truth SIF labels, candidate records were classified into **10 standardized Hazard / Energy Strata** based on energy source and physical mechanism:

| Hazard / Energy Mechanism Stratum | Total Candidates | Distribution (%) | Primary Annotation Sample (`BATCH_01`) |
| :--- | :---: | :---: | :---: |
| **Caught-in / Pinch / Rotating Machinery** | 6,672 | 25.25% | **499** |
| **Struck-by / Mobile Equipment / Falling Objects** | 5,605 | 21.21% | **501** |
| **Falls from Elevation / Gravity** | 4,540 | 17.18% | **450** |
| **Same-Level Slips / Trips** | 3,499 | 13.24% | **300** |
| **Other / Miscellaneous Hazards** | 3,888 | 14.71% | **102** |
| **Chemical / Toxic Inhalation** | 942 | 3.57% | **149** |
| **Thermal / Heat / Burn** | 766 | 2.90% | **200** |
| **Electrical Contact / Shock** | 194 | 0.73% | **191** |
| **Cardiovascular / Medical Event** | 179 | 0.68% | **49** |
| **Struck against Object** | 138 | 0.52% | **50** |
| **Total** | **26,423** | **100.00%** | **2,491** |

### Stratified Sampling Protocol
* The primary annotation batch (`is_candidate_sample == True`) comprises **2,491 high-value candidate records** across 2,476 distinct clusters.
* Selected whole clusters to guarantee that no matched pair is partially sampled.
* Enriched lower-frequency, high-consequence energy types (e.g., Electrical Shock, Thermal Burns, Chemical Inhalation) while maintaining robust representations of Falls, Caught-in, and Struck-by incidents.
* Balanced across sources: **634 records from OSHA HSE** (fatal/catastrophic investigations) and **1,857 records from OSHA Severe Injury** (hospitalizations/amputations).

---

## 7. Deliverables & Data Dictionary

The following prepared artifacts are saved directly in the project workspace:

### 7.1 Candidate Dataset: [`sif_annotation_candidates.csv`](file:///c:/SIH26165/sif_annotation_candidates.csv)
26,423 rows $\times$ 25 columns:
* `candidate_id`: Standardized unique primary key (`HSE_{summary_nr}_{idx}` / `SIR_{UPA}`).
* `source_dataset`: Origin tag (`osha_hse` or `osha_severe_injury`).
* `source_record_id`: Original incident identifier (`summary_nr` or `UPA`).
* `source_secondary_id`: Auxiliary identifier (Form 170 ID or `ID`).
* `original_row_index`: Zero-indexed row number in the raw CSV.
* `event_date`: Standardized `YYYY-MM-DD`.
* `normalized_narrative`: Normalized narrative with protected negation.
* `original_narrative`: Raw unaltered narrative.
* `event_headline`: Event summary headline (OSHA HSE).
* `event_keywords`: Precursor keyword tags (OSHA HSE).
* `hazard_stratum`: Standardized energy/hazard category.
* `source_event_code` & `source_event_title`: Original event code and title.
* `source_nature_title`: Original injury nature description.
* `source_part_title`: Original body part description.
* `source_equipment_source`: Original source of injury/environmental factor.
* `operational_context`: Task assignment, project type, or NAICS/Employer context.
* `reference_outcome_context`: Reference severity string (sequestered from labeling).
* `leak_prevention_cluster_id`: Cluster ID for leak-free train/validation/test splitting.
* `is_exact_duplicate`: Boolean exact duplicate flag.
* `is_near_duplicate`: Boolean near duplicate flag.
* `is_cross_dataset_match`: Boolean flag for confirmed 96 cross-dataset incident matches.
* `is_candidate_sample`: Boolean flag indicating inclusion in primary stratified sample pool.
* `candidate_stratum`: Stratum used during sampling.
* `sampling_batch`: `BATCH_01_PRIMARY` (2,491 records) vs. `UNSAMPLED_RESERVOIR` (23,932 records).

### 7.2 Duplicate Audit Table: [`duplicate_flags.csv`](file:///c:/SIH26165/duplicate_flags.csv)
310 flagged records detailing:
* `candidate_id`, `source_dataset`, `source_record_id`
* `duplicate_type`: `exact_duplicate`, `near_duplicate`, or `cross_dataset_semantic_match`
* `duplicate_group_id`: Unique group identifier
* `matched_candidate_id`: Counterpart candidate record
* `similarity_score`: Jaccard similarity coefficient (0.300 to 1.000)
* `flag_reason`: Explanation of duplicate detection criteria

### 7.3 Pipeline Summary Metadata: [`dataset_summary.json`](file:///c:/SIH26165/dataset_summary.json)
Machine-readable JSON containing pipeline configuration, raw vs. cleaned counts, text length statistics before and after normalization, cluster statistics, and stratification distributions.
