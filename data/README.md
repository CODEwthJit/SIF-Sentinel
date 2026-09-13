# SIF Sentinel — Training Dataset Provenance & Methodology

This directory documents the historical incident data and annotation pipelines used to train and evaluate the machine learning model in **SIF Sentinel**.

---

## 1. Runtime Independence Notice

> [!IMPORTANT]
> **Zero Local Dataset Dependency at Runtime**  
> SIF Sentinel performs real-time SIF precursor detection directly using the packaged, frozen ML baseline (`ml/tfidf_baseline_model.joblib` and `ml/tfidf_baseline_vectorizer.joblib`) and the symbolic V2.3 deterministic rule engine (`src/sif_auto_annotator_v23.py`).  
> **Raw and processed training datasets (~50 MB) are excluded from version control** because they are not required to run, test, or evaluate the application locally.

---

## 2. Dataset Sources & Overview

The offline models and annotation engines were developed using publicly available federal workplace safety datasets:

1. **OSHA Severe Injury Reports (SIR)**:
   - Source: U.S. Occupational Safety and Health Administration (OSHA)
   - Scope: Severe injury records documenting hospitalizations and amputations across general and construction industries.
2. **OSHA HSE Abstracts**:
   - Source: OSHA Accident Investigation Summaries
   - Scope: Textual abstracts describing high-severity fatal and catastrophic workplace incidents.
3. **OIICS (Occupational Injury and Illness Classification System)**:
   - Event and exposure reference codes used during initial stratification.

---

## 3. Data Pipeline & Annotation Architecture

```
Raw OSHA Narratives
        ↓
Data Cleaning & Normalization
(Stripped non-narrative metadata to enforce Metadata Quarantine)
        ↓
V2.3 Deterministic Rule Engine
(Gravity, Pressure, Electrical, Chemical, Machinery, Confined Space)
        ↓
Provisional SIF Precursor Labels (YES / NO / UNCERTAIN)
        ↓
TF-IDF Vectorization (4,886 n-grams) & Balanced Logistic Regression (C=100.0)
        ↓
Production Model Artifacts (ml/tfidf_baseline_*.joblib)
```

---

## 4. Metadata Quarantine Guarantee

During model training and inference, strict metadata quarantine was enforced:
- **No outcome data** (hospitalization, amputation, fatality indicators) was provided as input features.
- **Pure text only**: Features are derived exclusively from the descriptive incident narrative.
- This ensures the model identifies **precursors of potential severity** rather than memorizing resulting outcomes.

