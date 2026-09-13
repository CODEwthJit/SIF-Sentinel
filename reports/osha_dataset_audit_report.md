# Independent Audit Report: OSHA Incident & Severe Injury Datasets

**Audit Date:** September 2026  
**Auditor:** Antigravity AI  
**Datasets Analyzed:**
1. `OSHA HSE DATA_ALL ABSTRACTS 15-17_FINAL.csv` (OSHA Form 170 Investigation Abstracts, 2015–2017)
2. `severeinjury.csv` (OSHA Severe Injury Reports Database, 2015–2017)
3. `oiics_201_code_list.xlsx` (OSHA / BLS OIICS Version 2.01 Reference Codebook)

> **Integrity Confirmation:** All original source files remained completely untouched and unmodified. All calculations and exports were generated non-destructively.

---

## 1. Executive Summary & Core Dataset Metrics

| Metric | OSHA HSE Abstracts Dataset | OSHA Severe Injury Dataset |
| :--- | :--- | :--- |
| **Source File** | `OSHA HSE DATA_ALL ABSTRACTS 15-17_FINAL.csv` | `severeinjury.csv` |
| **Total Rows** | **4,847** | **21,578** |
| **Total Columns** | **29** | **26** |
| **File Size / Encoding** | 3.43 MB / UTF-8 | 10.99 MB / Latin-1 (CP1252) |
| **Primary Incident Key** | `summary_nr` (4,844 unique, 3 multi-victim duplicates) | `UPA` (21,578 unique, 0 duplicates) |
| **Secondary Identifiers** | Form 170 Inspection Summary ID | `ID` (21,573 unique, 5 duplicates), `Inspection` (7,770 unique) |
| **Date Coverage** | July 1, 2015 – August 10, 2017 | January 1, 2015 – February 28, 2017 |
| **Primary Scope / Nature** | Catastrophic & fatal workplace investigations (Form 170) | Employer-mandated severe injury self-reports (29 CFR 1904.39) |
| **Fatality Representation** | **61.15% Fatal** (2,964 fatal vs 1,883 non-fatal) | Non-fatal baseline (hospitalizations & amputations) |
| **Coding Taxonomy** | OSHA IMIS / Form 170 Legacy Codes (1–2 digits) | BLS / OSHA OIICS 2.01 Hierarchy (1–4 digits) |

---

## 2. Identifier Audit & Duplicate Analysis

### 2.1 OSHA HSE Abstracts (`summary_nr`)
* **Full-Row Duplicates:** `0`
* **Unique `summary_nr` Count:** `4,844`
* **Duplicate `summary_nr` Count:** `3` instances (representing multi-victim incidents):
  * `summary_nr 220873897`: 3 records from July 31, 2016 (same skid-steer loader incident with multiple workers).
  * `summary_nr 220957740`: 2 records from May 17, 2017 (caught between incident).
* **Finding:** In OSHA Form 170 records, `summary_nr` represents an *investigation case*. Multiple workers injured or killed in the same event share the same `summary_nr`.

### 2.2 OSHA Severe Injury Dataset (`ID`, `UPA`, `Inspection`)
* **Full-Row Duplicates:** `0`
* **Unique `UPA` (Unprogrammed Activity ID):** `21,578` (**100% unique**). `UPA` serves as the true primary key.
* **Unique `ID`:** `21,573` (5 duplicate ID numbers across distinct incidents due to re-indexing).
* **Inspection Tracking:** `7,822` non-null inspection records (`36.25%` of reports triggered a formal OSHA on-site inspection), representing `7,770` unique OSHA inspection IDs.

---

## 3. Data Completeness & Missing Value Profile

### 3.1 OSHA HSE Abstracts
* **Standard Nulls:**
  * `Nature of Injury`: 2 nulls (0.04%)
  * `Part of Body`: 2 nulls (0.04%)
  * `Event type`: 2 nulls (0.04%)
  * `Environmental Factor`: 7 nulls (0.14%)
  * `Human Factor`: 7 nulls (0.14%)
* **Hidden / Sparsely Populated Fields (Empty Strings & Zero Sentinel Values):**
  * `Construction End Use` (`con_end`): **78.81% empty** (3,820 rows blank). Populated only for construction projects.
  * `Project Type` (`proj_type`): **77.72% empty** (3,767 rows blank).
  * `Building Stories` (`build_stor`): **85.58% empty** (4,148 rows blank).
  * `Project Cost` (`proj_cost`): **87.91% empty** (4,261 rows blank).
  * `fall_ht`: **100% zero** (Mean = 0.0, Max = 0). Fall height must be extracted from the text narratives.

### 3.2 OSHA Severe Injury Dataset
* **High-Completeness Columns:** `EventDate`, `Employer`, `State`, `Hospitalized`, `Final Narrative`, `Nature`, `Part of Body`, `Event`, `Source` (all 100% populated).
* **Missing Value Rates:**
  * `Address2`: 19,717 missing (**91.38%**)
  * `Secondary Source` & `Secondary Source Title`: 15,766 missing (**73.07%**) (only logged when a secondary object contributed).
  * `Inspection`: 13,756 missing (**63.75%**) (uninspected self-reports).
  * `Latitude` / `Longitude`: 91 missing (0.42%)
  * `Zip`: 11 missing (0.05%)
  * `Address1`: 10 missing (0.05%)
  * `City`: 9 missing (0.04%)
  * `Primary NAICS`: 2 missing (0.01%)
  * `Amputation`: 2 missing (0.01%)

---

## 4. Narrative Fields & Text Length Statistics

Text narratives are the core input for natural language processing and SIF-precursor classification models.

### Narrative Length Comparison Table

| Dataset & Field | Total Non-Empty | Empty (%) | Char Min / Med / Max | Char Mean (Std) | Word Min / Med / Max | Word Mean (Std) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **OSHA HSE: `Abstract Text`** | 4,847 | 0.00% | 5 / **338** / 3,291 | **412.44** (282.13) | 1 / **59** / 538 | **71.82** (48.49) |
| **OSHA HSE: `Event Description`** | 4,847 | 0.00% | 17 / **51** / 60 | **49.89** (9.32) | 3 / **8** / 14 | **8.19** (1.63) |
| **OSHA HSE: `Event Keywords`** | 4,847 | 0.00% | 1 / **46** / 200 | **50.08** (26.88) | 1 / **3** / 14 | **3.04** (1.58) |
| **Severe: `Final Narrative`** | 21,578 | 0.00% | 4 / **168** / 1,247 | **187.01** (96.97) | 1 / **29** / 232 | **32.48** (17.21) |

#### Narrative Quality Insights:
1. **OSHA HSE `Abstract Text`:** Highly rich, inspector-drafted investigative summaries. At an average of 72 words (up to 538 words), they detail the sequence of events, tools used, victim positioning, and physical barriers that failed.
2. **OSHA HSE `Event Description`:** Standardized uppercase headline (capped at ~60 characters), ideal for rapid zero-shot hazard classification (e.g., `EMPLOYEE IS STRUCK BY FALLING TREE BRANCH AND IS KILLED`).
3. **OSHA HSE `Event Keywords`:** Comma-delimited expert keywords (e.g., `fall, roof, scaffold, fracture`), providing strong supervision for multi-label tagging.
4. **Severe Injury `Final Narrative`:** Employer-reported incident summaries. More concise (median 29 words) but focused directly on the point of contact, machinery caught-in, and immediate medical intervention.

---

## 5. Categorical Distributions (Injury, Mechanism, and Causation)

### 5.1 OSHA HSE Dataset
* **Degree of Injury:**
  * **Fatal:** `2,964` (61.15%)
  * **Nonfatal:** `1,883` (38.85%)
* **Event Type (Top 5):**
  1. Fall (from elevation): `1,179` (24.32%)
  2. Struck-by: `1,138` (23.48%)
  3. Caught in or between: `1,133` (23.38%)
  4. Other: `643` (13.27%)
  5. Shock (Electrical): `194` (4.00%)
* **Nature of Injury (Top 5):**
  1. Serious Fall/Strike: `1,683` (34.72%)
  2. Fracture, Broken Bones: `852` (17.58%)
  3. Amputation, Crushing: `542` (11.18%)
  4. Laceration: `382` (7.88%)
  5. Head Trauma: `328` (6.77%)
* **Human Factors / Operational Barriers (Top 5):**
  1. Other: `1,838` (37.92%)
  2. Misjudgment of Hazardous Situation: `1,398` (28.84%)
  3. Safety Devices Removed / Inoperable: `269` (5.55%)
  4. Position Inappropriate For Task: `219` (4.52%)
  5. Material-Handling Procedure Inappropriate: `154` (3.18%)
* **Task Assigned:**
  * Regularly Assigned: `3,048` (62.88%)
  * Not Regularly Assigned (Non-routine work): `1,799` (37.12%)

### 5.2 OSHA Severe Injury Dataset
* **Hospitalization Outcomes:**
  * 1 In-patient Hospitalization: `17,128` (79.38%)
  * 0 In-patient Hospitalizations (Amputation/Eye loss only): `4,298` (19.92%)
  * 2+ Hospitalizations: `152` (0.70%)
* **Amputation Outcomes:**
  * 0 Amputations: `15,789` (73.17%)
  * 1 Amputation: `5,764` (26.71%)
  * 2+ Amputations: `23` (0.11%)
* **Nature of Injury (OIICS Top 5):**
  1. Fractures: `6,018` (27.89%)
  2. Amputations: `5,833` (27.03%)
  3. Soreness, pain, hurt: `2,129` (9.87%)
  4. Cuts, lacerations: `1,023` (4.74%)
  5. Traumatic injuries, unspecified: `951` (4.41%)
* **Event / Mechanism (OIICS Top 5):**
  1. Caught in running equipment/machinery during regular operation: `1,893` (8.77%)
  2. Compressed or pinched by shifting objects: `1,483` (6.87%)
  3. Caught in running equipment/machinery during maintenance: `1,329` (6.16%)
  4. Fall to lower level, unspecified: `1,198` (5.55%)
  5. Fall on same level due to slipping: `992` (4.60%)
* **Primary Source / Equipment (OIICS Top 5):**
  1. Floor / ground surfaces: `1,857` (8.61%)
  2. Forklift, order picker, powered truck: `814` (3.77%)
  3. Ladders (all types): `921` (4.27%)
  4. Environmental heat: `556` (2.58%)
  5. Highway motorized vehicles: `444` (2.06%)

---

## 6. Dataset Overlap & Cross-Dataset Relationship

### 6.1 Identifiers & Direct Matching
* `summary_nr` vs `ID` / `UPA` / `Inspection`: **0 direct numeric matches**.
* **Reason:** The databases are managed under distinct administrative modules:
  * HSE dataset uses the **IMIS / OSHA Form 170** investigation abstract registry.
  * Severe Injury dataset uses the **OIS / SIR** severe injury web portal intake registry.

### 6.2 Temporal Overlap Window
* **Shared Timeframe:** July 1, 2015 – February 28, 2017 (20 months).
* **HSE Records in Window:** `3,679` rows (**75.9%** of HSE).
* **Severe Injury Records in Window:** `16,684` rows (**77.3%** of Severe Injury).
* **Shared Incident Dates:** `578` identical calendar dates.

### 6.3 Semantic Incident Matching
Using exact date alignment and text Jaccard n-gram matching on incident descriptions:
* **Confirmed Overlapping Incidents:** **96 cross-database pairs** (95 unique HSE abstracts matching 96 Severe Injury cases).
* **Inspection Correlation:** In **91.7%** of these matched cases, the Severe Injury record contains an `Inspection` number (compared to the baseline inspection rate of only **36.2%** in the severe injury dataset).
* **Operational Insight:** When an employer reports a severe hospitalization or amputation, and OSHA determines the situation warrants a formal on-site inspection/investigation, an OSHA Form 170 abstract is created. Thus, the HSE dataset acts as an in-depth investigative subset of the most critical high-potential incidents.

---

## 7. OSHA Codebook (`oiics_201_code_list.xlsx`) Inspection & Mapping

The provided workbook contains 4 canonical classification sheets from the **Occupational Injury and Illness Classification System (OIICS) Version 2.01**:

| Codebook Sheet | Codebook Rows | Structure & Level | Severe Injury Dataset Alignment | HSE Abstracts Dataset Alignment |
| :--- | :---: | :--- | :--- | :--- |
| **`Nature`** | 615 | 1–4 digits (Hierarchy Level 1–4) | `Nature` column (**100% exact match**, 149 codes) | Corresponds to `nature_of_inj` (Legacy IMIS 1–22) |
| **`Part`** | 218 | 1–4 digits (Hierarchy Level 1–4) | `Part of Body` column (**100% exact match**, 118 codes) | Corresponds to `part_of_body` (Legacy IMIS 1–31) |
| **`Event`** | 537 | 1–4 digits (Hierarchy Level 1–4) | `Event` column (**100% exact match**, 306 codes) | Corresponds to `event_type` (Legacy IMIS 1–14) |
| **`Source`** | 1,665 | 1–4 digits (Hierarchy Level 1–4) | `Source` & `Secondary Source` (**100% exact match**) | Corresponds to `evn_factor` & `hazsub` |

> **Key Architectural Distinction:** `severeinjury.csv` adheres directly to the modern BLS/OSHA OIICS 2.01 hierarchical standard. In contrast, `OSHA HSE DATA_ALL ABSTRACTS 15-17_FINAL.csv` uses older OSHA IMIS Form 170 codes. Both datasets contain text titles alongside code values, enabling straightforward cross-system ontology mapping.

---

## 8. SIF-Precursor Annotation Framework Support

A **Significant Injury and Fatality (SIF) precursor** is defined as an event, condition, or high-energy hazard where safety controls/barriers are absent, ineffective, or compromised, which could lead to fatal or life-altering harm.

### Recommended Column Mapping Matrix

| SIF Dimension | Primary Columns (HSE) | Primary Columns (Severe Injury) | Annotation Framework Role |
| :--- | :--- | :--- | :--- |
| **1. Incident Narrative** | `Abstract Text`, `Event Description` | `Final Narrative` | Primary unstructured text for LLM/NLP precursor extraction and causal graph parsing. |
| **2. High-Energy Category** | `Event type` (Falls, Struck-by, Caught-in, Shock) | `Event` / `EventTitle`, `Source` / `SourceTitle` | Maps directly to the Energy Wheel (Gravity, Motion, Mechanical, Electrical, Chemical). |
| **3. Barrier / Control Failure** | `Human Factor`, `Environmental Factor` | `Secondary Source`, `EventTitle` | Captures procedural shortcuts, removed guards, missing PPE, and mechanical failure modes. |
| **4. Operational Context** | `Task Assigned` (Regular vs Non-routine), `Project Type` | `Primary NAICS` | Differentiates non-routine operations (a recognized SIF multiplier) and industry sector risk. |
| **5. Precursor Keyword Anchors** | `Event Keywords` | *Derived from text* | Pre-extracted tokens for model supervision and validation. |
| **6. Outcome Severity (SIF-Actual)**| `Degree of Injury` (Fatal vs Nonfatal) | `Hospitalized`, `Amputation` | Ground-truth labels separating SIF-Actual from SIF-Potential. |

---

## 9. Deliverables & Artifact Inventory

The following structured audit outputs have been generated and saved directly to the project root:

1. [`osha_dataset_audit_results.json`](file:///c:/SIH26165/osha_dataset_audit_results.json): Master structured JSON containing all audit metrics, distributions, narrative lengths, and overlap statistics.
2. [`hse_column_audit.csv`](file:///c:/SIH26165/hse_column_audit.csv): Column-by-column profile for OSHA HSE Abstracts (data types, missing rates, empty string counts, unique values, top distributions).
3. [`severeinjury_column_audit.csv`](file:///c:/SIH26165/severeinjury_column_audit.csv): Column-by-column profile for OSHA Severe Injury dataset.
4. [`sif_framework_columns.csv`](file:///c:/SIH26165/sif_framework_columns.csv): Detailed mapping of dataset columns to SIF precursor dimensions.
5. [`codebook_mapping_summary.csv`](file:///c:/SIH26165/codebook_mapping_summary.csv): Crosswalk table between OIICS 2.01 codebook sheets and dataset attributes.
