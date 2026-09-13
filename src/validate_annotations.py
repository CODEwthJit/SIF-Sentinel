#!/usr/bin/env python3
"""
validate_annotations.py
=======================
Validation script for SIF Precursor Annotations (SIH26165).

Validates sif_annotations.csv against sif_annotation_candidates.csv:
1. Candidate count preservation (matches original 2,491 sample rows)
2. Candidate IDs preservation and uniqueness (zero duplicate candidate_ids)
3. Allowed values for sif_label (YES, NO, UNCERTAIN)
4. Allowed values for barrier_failure (MISSING, BYPASSED, INADEQUATE, NOT_FOLLOWED, DEGRADED, NONE, UNKNOWN)
5. Allowed values for human_exposure (DIRECT, POTENTIAL, NONE, UNKNOWN)
6. Allowed values for annotation_confidence (HIGH, MEDIUM, LOW)
7. Required fields when annotated (evidence_text required for YES and NO)
8. Updates annotation_progress.json with accurate real-time metrics
"""

import sys
import json
import os
import pandas as pd
import numpy as np

# Allowed controlled vocabularies
ALLOWED_SIF_LABELS = {"YES", "NO", "UNCERTAIN"}
ALLOWED_BARRIER_FAILURES = {
    "MISSING", "BYPASSED", "INADEQUATE", "NOT_FOLLOWED",
    "DEGRADED", "NONE", "UNKNOWN"
}
ALLOWED_HUMAN_EXPOSURES = {"DIRECT", "POTENTIAL", "NONE", "UNKNOWN"}
ALLOWED_CONFIDENCES = {"HIGH", "MEDIUM", "LOW"}

CANDIDATES_CSV = "sif_annotation_candidates.csv"
ANNOTATIONS_CSV = "sif_annotations.csv"
PROGRESS_JSON = "annotation_progress.json"

def validate(annotations_path=ANNOTATIONS_CSV, candidates_path=CANDIDATES_CSV, progress_path=PROGRESS_JSON):
    print("=" * 65)
    print("SIF PRECURSOR ANNOTATION VALIDATION")
    print("=" * 65)
    
    errors = []
    warnings = []
    
    # Check file existence
    if not os.path.exists(annotations_path):
        print(f"CRITICAL ERROR: Annotations file '{annotations_path}' not found.")
        sys.exit(1)
        
    if not os.path.exists(candidates_path):
        print(f"CRITICAL ERROR: Candidates file '{candidates_path}' not found.")
        sys.exit(1)
        
    # 1. Load files
    df_cand = pd.read_csv(candidates_path, low_memory=False)
    expected_sample = df_cand[df_cand['is_candidate_sample'] == True].copy()
    expected_count = len(expected_sample)
    expected_ids = list(expected_sample['candidate_id'])
    
    df_ann = pd.read_csv(annotations_path, low_memory=False, keep_default_na=False)
    actual_count = len(df_ann)
    
    print(f"Expected Sample Candidates Count: {expected_count}")
    print(f"Actual Annotations File Rows:     {actual_count}")
    
    # 2. Check row count
    if actual_count != expected_count:
        errors.append(f"Row count mismatch: expected {expected_count} rows, found {actual_count} rows.")
    else:
        print("  [PASS] Candidate row count is unchanged.")
        
    # 3. Check candidate_id uniqueness and preservation
    actual_ids = list(df_ann['candidate_id'])
    dup_ids = df_ann[df_ann['candidate_id'].duplicated(keep=False)]['candidate_id'].tolist()
    if dup_ids:
        errors.append(f"Duplicate candidate_ids found: {set(dup_ids)}")
    else:
        print("  [PASS] Zero duplicate candidate_ids found.")
        
    missing_ids = set(expected_ids) - set(actual_ids)
    extra_ids = set(actual_ids) - set(expected_ids)
    if missing_ids:
        errors.append(f"Missing expected candidate IDs ({len(missing_ids)} IDs missing, e.g. {list(missing_ids)[:3]})")
    if extra_ids:
        errors.append(f"Unexpected extra candidate IDs found ({len(extra_ids)} extra IDs, e.g. {list(extra_ids)[:3]})")
        
    if not missing_ids and not extra_ids:
        print("  [PASS] All candidate IDs are perfectly preserved.")
        
    # 4. Check schema preservation
    expected_cols = list(expected_sample.columns)
    required_new_cols = [
        'sif_label', 'hazard_energy', 'activity', 'barrier_control',
        'barrier_failure', 'human_exposure', 'potential_consequence',
        'lsr_tags', 'evidence_text', 'annotation_confidence',
        'annotation_notes', 'annotator_id'
    ]
    for c in expected_cols:
        if c not in df_ann.columns:
            errors.append(f"Original candidate column '{c}' is missing from annotations table.")
    for c in required_new_cols:
        if c not in df_ann.columns:
            errors.append(f"Required annotation column '{c}' is missing from annotations table.")
            
    # 5. Row-level validation of annotation fields
    annotated_rows = 0
    yes_count = 0
    no_count = 0
    uncertain_count = 0
    high_conf = 0
    med_conf = 0
    low_conf = 0
    
    for idx, row in df_ann.iterrows():
        cid = row['candidate_id']
        raw_label = str(row['sif_label']).strip() if pd.notnull(row['sif_label']) else ""
        raw_label = "" if raw_label.lower() in ['nan', 'null'] else raw_label
        
        # If unannotated, skip field-level strict checks
        if not raw_label:
            continue
            
        annotated_rows += 1
        label = raw_label.upper()
        
        # SIF label check
        if label not in ALLOWED_SIF_LABELS:
            errors.append(f"Row {idx} (ID: {cid}): Invalid sif_label '{raw_label}'. Allowed: {sorted(ALLOWED_SIF_LABELS)}")
        else:
            if label == 'YES':
                yes_count += 1
            elif label == 'NO':
                no_count += 1
            elif label == 'UNCERTAIN':
                uncertain_count += 1
                
        # evidence_text check (REQUIRED for YES and NO)
        raw_evidence = str(row['evidence_text']).strip() if pd.notnull(row['evidence_text']) else ""
        raw_evidence = "" if raw_evidence.lower() in ['nan', 'null'] else raw_evidence
        
        if label in {'YES', 'NO'}:
            if not raw_evidence:
                errors.append(f"Row {idx} (ID: {cid}): evidence_text is required when sif_label is '{label}', but was empty.")
            else:
                # verify evidence text comes from narrative or headline
                narrative = str(row['normalized_narrative']).lower()
                headline = str(row['event_headline']).lower()
                ev_clean = raw_evidence.lower()
                # Check for substantial overlap (do not invent evidence)
                # First 20 chars or subset
                if len(ev_clean) >= 10 and (ev_clean not in narrative and ev_clean not in headline) and not any(part in narrative or part in headline for part in ev_clean.split() if len(part) >= 4):
                    warnings.append(f"Row {idx} (ID: {cid}): evidence_text '{raw_evidence[:30]}...' may not directly match narrative words.")
                    
        # barrier_failure check
        raw_bf = str(row['barrier_failure']).strip().upper() if pd.notnull(row['barrier_failure']) else ""
        raw_bf = "" if raw_bf in ['NAN', 'NULL'] else raw_bf
        if raw_bf and raw_bf not in ALLOWED_BARRIER_FAILURES:
            errors.append(f"Row {idx} (ID: {cid}): Invalid barrier_failure '{row['barrier_failure']}'. Allowed: {sorted(ALLOWED_BARRIER_FAILURES)}")
            
        # human_exposure check
        raw_he = str(row['human_exposure']).strip().upper() if pd.notnull(row['human_exposure']) else ""
        raw_he = "" if raw_he in ['NAN', 'NULL'] else raw_he
        if raw_he and raw_he not in ALLOWED_HUMAN_EXPOSURES:
            errors.append(f"Row {idx} (ID: {cid}): Invalid human_exposure '{row['human_exposure']}'. Allowed: {sorted(ALLOWED_HUMAN_EXPOSURES)}")
            
        # annotation_confidence check
        raw_conf = str(row['annotation_confidence']).strip().upper() if pd.notnull(row['annotation_confidence']) else ""
        raw_conf = "" if raw_conf in ['NAN', 'NULL'] else raw_conf
        if raw_conf:
            if raw_conf not in ALLOWED_CONFIDENCES:
                errors.append(f"Row {idx} (ID: {cid}): Invalid annotation_confidence '{row['annotation_confidence']}'. Allowed: {sorted(ALLOWED_CONFIDENCES)}")
            else:
                if raw_conf == 'HIGH':
                    high_conf += 1
                elif raw_conf == 'MEDIUM':
                    med_conf += 1
                elif raw_conf == 'LOW':
                    low_conf += 1
        elif raw_label:
            errors.append(f"Row {idx} (ID: {cid}): annotation_confidence is missing for annotated row.")

    # 6. Summary and Progress JSON update
    unannotated_rows = actual_count - annotated_rows
    progress_data = {
        "total_candidates": actual_count,
        "annotated_count": annotated_rows,
        "unannotated_count": unannotated_rows,
        "yes_count": yes_count,
        "no_count": no_count,
        "uncertain_count": uncertain_count,
        "high_confidence_count": high_conf,
        "medium_confidence_count": med_conf,
        "low_confidence_count": low_conf
    }
    
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress_data, f, indent=2)
        
    print("-" * 65)
    print("ANNOTATION PROGRESS METRICS:")
    print(f"  Total Candidates:    {actual_count}")
    print(f"  Annotated Count:     {annotated_rows} ({(annotated_rows/actual_count*100):.1f}%)")
    print(f"  Unannotated Count:   {unannotated_rows} ({(unannotated_rows/actual_count*100):.1f}%)")
    print(f"  YES Count:           {yes_count}")
    print(f"  NO Count:            {no_count}")
    print(f"  UNCERTAIN Count:     {uncertain_count}")
    print(f"  HIGH Confidence:     {high_conf}")
    print(f"  MEDIUM Confidence:   {med_conf}")
    print(f"  LOW Confidence:      {low_conf}")
    print("-" * 65)
    
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings[:5]:
            print(f"  [WARN] {w}")
        if len(warnings) > 5:
            print(f"  ... and {len(warnings) - 5} more warnings.")
            
    if errors:
        print(f"\nVALIDATION FAILED ({len(errors)} errors found):")
        for e in errors[:15]:
            print(f"  [ERROR] {e}")
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more errors.")
        print(f"\nResult: FAILED (Errors: {len(errors)})")
        return False
    else:
        print("\nResult: PASSED (All validation constraints satisfied)")
        print(f"Progress file '{progress_path}' updated successfully.")
        return True

if __name__ == "__main__":
    target_path = sys.argv[1] if len(sys.argv) > 1 else ANNOTATIONS_CSV
    success = validate(annotations_path=target_path)
    sys.exit(0 if success else 1)
