"""
TF-IDF + Logistic Regression Baseline for SIF Precursor Detection
Phase 6.1 — SIH26165

Strict Narrative-Only Feature Modeling:
Evaluates whether normalized incident narratives alone contain sufficient
information to reproduce the frozen V2.3 deterministic SIF annotations.

Rules strictly enforced:
- Zero metadata features (no outcome context, event codes, titles, energies, or barriers).
- Leakage-aware splitting (GroupShuffleSplit on leak_prevention_cluster_id).
- TF-IDF fitted strictly on training data.
- Hyperparameter C and decision threshold tuned strictly on validation data.
- Untouched test evaluation.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    classification_report
)

# ---------------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
# ---------------------------------------------------------------------------
DATASET_PATH = os.path.join("data", "processed", "sif_annotations_v23.csv")
OUTPUT_DIR = "ml"
RANDOM_SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

TFIDF_CONFIG = {
    "ngram_range": (1, 2),
    "min_df": 2,
    "max_features": 5000,
    "sublinear_tf": True,
    "strip_accents": "unicode",
    "lowercase": True
}

LOGREG_C_CANDIDATES = [0.01, 0.1, 1.0, 10.0, 100.0]
THRESHOLD_RANGE = np.arange(0.30, 0.71, 0.01)


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_and_prepare_data():
    """
    Loads dataset, isolates binary records (YES / NO), excluding UNCERTAIN.
    Validates metadata quarantine.
    """
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

    raw_df = pd.read_csv(DATASET_PATH)
    total_records = len(raw_df)

    # Determine target column (sif_label_v23 or sif_label)
    target_col = "sif_label_v23" if "sif_label_v23" in raw_df.columns else "sif_label"
    
    # Exclude UNCERTAIN records
    uncertain_count = (raw_df[target_col] == "UNCERTAIN").sum()
    binary_df = raw_df[raw_df[target_col].isin(["YES", "NO"])].copy().reset_index(drop=True)
    binary_count = len(binary_df)
    yes_count = (binary_df[target_col] == "YES").sum()
    no_count = (binary_df[target_col] == "NO").sum()

    print(f"[DATA] Total raw records: {total_records}")
    print(f"[DATA] Excluded UNCERTAIN records: {uncertain_count}")
    print(f"[DATA] Retained binary records: {binary_count} (YES: {yes_count}, NO: {no_count})")

    # Binary target: YES -> 1, NO -> 0
    binary_df["target"] = (binary_df[target_col] == "YES").astype(int)

    # STRICT FEATURE ISOLATION VERIFICATION
    # Ensure ONLY normalized_narrative is passed to the ML pipeline
    narrative_col = "normalized_narrative"
    assert narrative_col in binary_df.columns, f"Missing required column: {narrative_col}"
    assert binary_df[narrative_col].isna().sum() == 0, "Null narratives found!"

    # Cluster column for leakage-free splitting
    cluster_col = "leak_prevention_cluster_id"
    assert cluster_col in binary_df.columns, f"Missing required cluster column: {cluster_col}"

    return raw_df, binary_df, target_col, cluster_col, narrative_col


def split_data(binary_df, cluster_col):
    """
    Performs leakage-aware 70/15/15 split using GroupShuffleSplit on leak_prevention_cluster_id.
    Ensures zero cluster overlap across train, validation, and test partitions.
    """
    # Step 1: Split train (70%) vs temp (30%)
    gss_train = GroupShuffleSplit(n_splits=1, train_size=TRAIN_RATIO, random_state=RANDOM_SEED)
    train_idx, temp_idx = next(gss_train.split(binary_df, groups=binary_df[cluster_col]))

    train_df = binary_df.iloc[train_idx].copy().reset_index(drop=True)
    temp_df = binary_df.iloc[temp_idx].copy().reset_index(drop=True)

    # Step 2: Split temp equally into validation (15%) and test (15%)
    gss_val_test = GroupShuffleSplit(n_splits=1, train_size=0.50, random_state=RANDOM_SEED)
    val_idx, test_idx = next(gss_val_test.split(temp_df, groups=temp_df[cluster_col]))

    val_df = temp_df.iloc[val_idx].copy().reset_index(drop=True)
    test_df = temp_df.iloc[test_idx].copy().reset_index(drop=True)

    # Verification of zero leakage
    train_clusters = set(train_df[cluster_col])
    val_clusters = set(val_df[cluster_col])
    test_clusters = set(test_df[cluster_col])

    overlap_train_val = len(train_clusters.intersection(val_clusters))
    overlap_train_test = len(train_clusters.intersection(test_clusters))
    overlap_val_test = len(val_clusters.intersection(test_clusters))

    assert overlap_train_val == 0, f"Leakage detected between train and val: {overlap_train_val}"
    assert overlap_train_test == 0, f"Leakage detected between train and test: {overlap_train_test}"
    assert overlap_val_test == 0, f"Leakage detected between val and test: {overlap_val_test}"

    print("\n[SPLIT] Leakage-aware split completed successfully (zero cluster crossover):")
    for name, split in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
        n_tot = len(split)
        n_yes = (split["target"] == 1).sum()
        n_no = (split["target"] == 0).sum()
        pct_yes = (n_yes / n_tot) * 100.0
        print(f"  {name:5s}: Total={n_tot:3d} | YES={n_yes:3d} ({pct_yes:.1f}%) | NO={n_no:3d} ({100-pct_yes:.1f}%) | Clusters={split[cluster_col].nunique()}")

    return train_df, val_df, test_df


def train_and_select_hyperparameters(train_df, val_df, narrative_col):
    """
    Fits TF-IDF strictly on training data.
    Sweeps C over validation set only to find optimal regularization parameter.
    """
    # STRICT TF-IDF FIT ON TRAIN ONLY
    vectorizer = TfidfVectorizer(**TFIDF_CONFIG)
    X_train = vectorizer.fit_transform(train_df[narrative_col])
    X_val = vectorizer.transform(val_df[narrative_col])

    y_train = train_df["target"].values
    y_val = val_df["target"].values

    vocab_size = len(vectorizer.vocabulary_)
    non_zero_features = X_train.nnz
    sparsity = 1.0 - (non_zero_features / (X_train.shape[0] * X_train.shape[1]))

    print(f"\n[TF-IDF] Fit on Train strictly:")
    print(f"  Vocabulary size: {vocab_size}")
    print(f"  X_train shape: {X_train.shape}")
    print(f"  Non-zero elements: {non_zero_features} (sparsity: {sparsity*100:.2f}%)")

    # Hyperparameter selection on validation set
    val_results = []
    best_c = None
    best_val_macro_f1 = -1.0
    best_model = None

    print("\n[HYPERPARAMETER SWEEP] Evaluating C on Validation Set (threshold=0.50):")
    for c in LOGREG_C_CANDIDATES:
        clf = LogisticRegression(
            C=c,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            max_iter=1000
        )
        clf.fit(X_train, y_train)

        val_probs = clf.predict_proba(X_val)[:, 1]
        val_preds = (val_probs >= 0.50).astype(int)

        acc = accuracy_score(y_val, val_preds)
        macro_p = precision_score(y_val, val_preds, average="macro", zero_division=0)
        macro_r = recall_score(y_val, val_preds, average="macro", zero_division=0)
        macro_f1 = f1_score(y_val, val_preds, average="macro", zero_division=0)
        roc_auc = roc_auc_score(y_val, val_probs)
        pr_auc = average_precision_score(y_val, val_probs)

        record = {
            "C": c,
            "accuracy": float(acc),
            "macro_precision": float(macro_p),
            "macro_recall": float(macro_r),
            "macro_f1": float(macro_f1),
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc)
        }
        val_results.append(record)
        print(f"  C={c:6.2f} | Acc={acc:.4f} | Macro-F1={macro_f1:.4f} | Macro-Rec={macro_r:.4f} | ROC-AUC={roc_auc:.4f} | PR-AUC={pr_auc:.4f}")

        if macro_f1 > best_val_macro_f1:
            best_val_macro_f1 = macro_f1
            best_c = c
            best_model = clf

    print(f"[HYPERPARAMETER SELECTION] Selected C={best_c} (Validation Macro F1 = {best_val_macro_f1:.4f})")
    return vectorizer, best_model, best_c, val_results, X_train, y_train, X_val, y_val


def sweep_and_lock_threshold(best_model, X_val, y_val):
    """
    Performs a validation-only threshold sweep from 0.30 to 0.70.
    Selects threshold based on Macro F1 (tie-breaker: YES recall).
    Locks the threshold.
    """
    val_probs = best_model.predict_proba(X_val)[:, 1]

    best_threshold = 0.50
    best_macro_f1 = -1.0
    best_yes_recall = -1.0
    threshold_sweep_records = []

    for t in THRESHOLD_RANGE:
        t_rounded = round(float(t), 2)
        preds = (val_probs >= t_rounded).astype(int)

        macro_f1 = f1_score(y_val, preds, average="macro", zero_division=0)
        yes_recall = recall_score(y_val, preds, pos_label=1, zero_division=0)
        yes_precision = precision_score(y_val, preds, pos_label=1, zero_division=0)
        yes_f1 = f1_score(y_val, preds, pos_label=1, zero_division=0)
        no_recall = recall_score(y_val, preds, pos_label=0, zero_division=0)
        no_precision = precision_score(y_val, preds, pos_label=0, zero_division=0)
        no_f1 = f1_score(y_val, preds, pos_label=0, zero_division=0)
        acc = accuracy_score(y_val, preds)

        threshold_sweep_records.append({
            "threshold": t_rounded,
            "accuracy": float(acc),
            "macro_f1": float(macro_f1),
            "yes_recall": float(yes_recall),
            "yes_precision": float(yes_precision),
            "yes_f1": float(yes_f1),
            "no_recall": float(no_recall),
            "no_precision": float(no_precision),
            "no_f1": float(no_f1)
        })

        # Selection criterion: primary = Macro F1, tie-breaker = YES recall
        if (macro_f1 > best_macro_f1) or (np.isclose(macro_f1, best_macro_f1) and yes_recall > best_yes_recall):
            best_macro_f1 = macro_f1
            best_yes_recall = yes_recall
            best_threshold = t_rounded

    print(f"\n[THRESHOLD SWEEP] Validation sweep from 0.30 to 0.70 complete.")
    print(f"[THRESHOLD LOCKED] Locked threshold = {best_threshold:.2f} (Val Macro F1 = {best_macro_f1:.4f}, Val YES Recall = {best_yes_recall:.4f})")

    return best_threshold, threshold_sweep_records


def evaluate_test_set(best_model, vectorizer, test_df, narrative_col, locked_threshold):
    """
    Evaluates untouched test partition using the locked threshold.
    Generates all final test metrics, confusion matrix, ROC curve, and PR curve.
    """
    X_test = vectorizer.transform(test_df[narrative_col])
    y_test = test_df["target"].values

    test_probs = best_model.predict_proba(X_test)[:, 1]
    test_preds = (test_probs >= locked_threshold).astype(int)

    acc = accuracy_score(y_test, test_preds)
    macro_p = precision_score(y_test, test_preds, average="macro", zero_division=0)
    macro_r = recall_score(y_test, test_preds, average="macro", zero_division=0)
    macro_f1 = f1_score(y_test, test_preds, average="macro", zero_division=0)

    yes_p = precision_score(y_test, test_preds, pos_label=1, zero_division=0)
    yes_r = recall_score(y_test, test_preds, pos_label=1, zero_division=0)
    yes_f1 = f1_score(y_test, test_preds, pos_label=1, zero_division=0)

    no_p = precision_score(y_test, test_preds, pos_label=0, zero_division=0)
    no_r = recall_score(y_test, test_preds, pos_label=0, zero_division=0)
    no_f1 = f1_score(y_test, test_preds, pos_label=0, zero_division=0)

    roc_auc = roc_auc_score(y_test, test_probs)
    pr_auc = average_precision_score(y_test, test_probs)
    cm = confusion_matrix(y_test, test_preds)  # [[TN, FP], [FN, TP]]

    metrics = {
        "accuracy": float(acc),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "macro_f1": float(macro_f1),
        "yes_precision": float(yes_p),
        "yes_recall": float(yes_r),
        "yes_f1": float(yes_f1),
        "no_precision": float(no_p),
        "no_recall": float(no_r),
        "no_f1": float(no_f1),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "confusion_matrix": {
            "true_no_pred_no (TN)": int(cm[0, 0]),
            "true_no_pred_yes (FP)": int(cm[0, 1]),
            "true_yes_pred_no (FN)": int(cm[1, 0]),
            "true_yes_pred_yes (TP)": int(cm[1, 1])
        }
    }

    print("\n" + "="*60)
    print("FINAL UNTOUCHED TEST SET PERFORMANCE (Locked Threshold)")
    print("="*60)
    print(f"Accuracy:         {acc:.4f}")
    print(f"Macro Precision:  {macro_p:.4f}")
    print(f"Macro Recall:     {macro_r:.4f}")
    print(f"Macro F1:         {macro_f1:.4f}")
    print(f"YES Precision:    {yes_p:.4f} | YES Recall: {yes_r:.4f} | YES F1: {yes_f1:.4f}")
    print(f"NO Precision:     {no_p:.4f} | NO Recall:  {no_r:.4f} | NO F1:  {no_f1:.4f}")
    print(f"ROC-AUC:          {roc_auc:.4f}")
    print(f"PR-AUC:           {pr_auc:.4f}")
    print(f"\nConfusion Matrix (Rows=True, Cols=Predicted):\n{cm}")
    print("="*60)

    # 1. Plot Confusion Matrix
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    classes = ["NO (0)", "YES (1)"]
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=classes, yticklabels=classes,
           title=f'Test Confusion Matrix (Threshold = {locked_threshold:.2f})',
           ylabel='True SIF Label',
           xlabel='Predicted SIF Label')
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontweight="bold")
    fig.tight_layout()
    cm_path = os.path.join(OUTPUT_DIR, "tfidf_baseline_confusion_matrix.png")
    fig.savefig(cm_path, dpi=300)
    plt.close(fig)

    # 2. Plot ROC Curve
    fpr, tpr, _ = roc_curve(y_test, test_probs)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC Curve (AUC = {roc_auc:.4f})')
    ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Chance Level')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate (1 - Specificity)')
    ax.set_ylabel('True Positive Rate (Recall)')
    ax.set_title('Receiver Operating Characteristic (ROC) — Test Set')
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    roc_path = os.path.join(OUTPUT_DIR, "tfidf_baseline_roc.png")
    fig.savefig(roc_path, dpi=300)
    plt.close(fig)

    # 3. Plot Precision-Recall Curve
    precision_curve, recall_curve, _ = precision_recall_curve(y_test, test_probs)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall_curve, precision_curve, color='teal', lw=2, label=f'PR Curve (AP = {pr_auc:.4f})')
    baseline_pr = (y_test == 1).sum() / len(y_test)
    ax.plot([0, 1], [baseline_pr, baseline_pr], color='grey', lw=2, linestyle='--', label=f'Class Prior ({baseline_pr:.2f})')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title('Precision-Recall (PR) Curve — Test Set')
    ax.legend(loc="lower left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    pr_path = os.path.join(OUTPUT_DIR, "tfidf_baseline_pr.png")
    fig.savefig(pr_path, dpi=300)
    plt.close(fig)

    # 4. Predictions DataFrame
    pred_df = pd.DataFrame({
        "candidate_id": test_df["candidate_id"],
        "normalized_narrative": test_df[narrative_col],
        "true_label": np.where(y_test == 1, "YES", "NO"),
        "predicted_label": np.where(test_preds == 1, "YES", "NO"),
        "predicted_score": test_probs
    })
    pred_path = os.path.join(OUTPUT_DIR, "tfidf_baseline_test_predictions.csv")
    pred_df.to_csv(pred_path, index=False)

    return metrics, pred_df


def run_error_analysis(pred_df, test_df):
    """
    Identifies False Positives, False Negatives, highest-confidence errors,
    and categorizes them across failure archetypes.
    """
    merged = pred_df.copy()
    reason_col = "reason_code_v23" if "reason_code_v23" in test_df.columns else "reason_code"
    if reason_col in test_df.columns:
        merged[reason_col] = test_df[reason_col].values

    fps = merged[(merged["true_label"] == "NO") & (merged["predicted_label"] == "YES")].sort_values(by="predicted_score", ascending=False)
    fns = merged[(merged["true_label"] == "YES") & (merged["predicted_label"] == "NO")].sort_values(by="predicted_score", ascending=True)

    print("\n" + "="*60)
    print(f"ERROR ANALYSIS: {len(fps)} False Positives, {len(fns)} False Negatives")
    print("="*60)

    print("\n--- FALSE POSITIVES (True: NO, Predicted: YES) ---")
    for idx, row in fps.iterrows():
        print(f"ID: {row['candidate_id']} | Score: {row['predicted_score']:.4f} | Reason: {row.get(reason_col, 'N/A')}")
        print(f"Narrative: {row['normalized_narrative']}")
        print()

    print("--- FALSE NEGATIVES (True: YES, Predicted: NO) ---")
    for idx, row in fns.iterrows():
        print(f"ID: {row['candidate_id']} | Score: {row['predicted_score']:.4f} | Reason: {row.get(reason_col, 'N/A')}")
        print(f"Narrative: {row['normalized_narrative']}")
        print()

    return fps, fns


def main():
    ensure_output_dir()
    print("="*70)
    print("PHASE 6.1 — TF-IDF + LOGISTIC REGRESSION BASELINE PIPELINE")
    print("="*70)

    # 1. Load Data
    raw_df, binary_df, target_col, cluster_col, narrative_col = load_and_prepare_data()

    # 2. Split Data (Leakage-Aware)
    train_df, val_df, test_df = split_data(binary_df, cluster_col)

    # 3. Train & Select C on Validation Set
    vectorizer, best_model, best_c, val_results, X_train, y_train, X_val, y_val = train_and_select_hyperparameters(
        train_df, val_df, narrative_col
    )

    # 4. Sweep and Lock Threshold on Validation Set
    locked_threshold, threshold_sweep_records = sweep_and_lock_threshold(best_model, X_val, y_val)

    # 5. Evaluate Untouched Test Set
    metrics, pred_df = evaluate_test_set(best_model, vectorizer, test_df, narrative_col, locked_threshold)

    # 6. Error Analysis
    fps, fns = run_error_analysis(pred_df, test_df)

    # 7. Save Models and Configs
    model_path = os.path.join(OUTPUT_DIR, "tfidf_baseline_model.joblib")
    vec_path = os.path.join(OUTPUT_DIR, "tfidf_baseline_vectorizer.joblib")
    joblib.dump(best_model, model_path)
    joblib.dump(vectorizer, vec_path)

    metrics_path = os.path.join(OUTPUT_DIR, "tfidf_baseline_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    import sklearn
    config = {
        "experiment": "Phase 6.1 TF-IDF + Logistic Regression Baseline",
        "random_seed": RANDOM_SEED,
        "python_version": sys.version,
        "environment": {
            "sklearn_version": sklearn.__version__,
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__
        },
        "dataset": {
            "path": DATASET_PATH,
            "total_records": len(raw_df),
            "excluded_uncertain": int((raw_df[target_col] == "UNCERTAIN").sum()),
            "total_binary_usable": len(binary_df),
            "binary_yes": int((binary_df["target"] == 1).sum()),
            "binary_no": int((binary_df["target"] == 0).sum())
        },
        "splits": {
            "train": {"total": len(train_df), "yes": int((train_df["target"] == 1).sum()), "no": int((train_df["target"] == 0).sum()), "clusters": int(train_df[cluster_col].nunique())},
            "validation": {"total": len(val_df), "yes": int((val_df["target"] == 1).sum()), "no": int((val_df["target"] == 0).sum()), "clusters": int(val_df[cluster_col].nunique())},
            "test": {"total": len(test_df), "yes": int((test_df["target"] == 1).sum()), "no": int((test_df["target"] == 0).sum()), "clusters": int(test_df[cluster_col].nunique())}
        },
        "features": {
            "feature_source": "strict normalized_narrative only",
            "metadata_quarantined": True
        },
        "tfidf_config": TFIDF_CONFIG,
        "vocabulary_size": len(vectorizer.vocabulary_),
        "selected_hyperparameters": {
            "C": best_c,
            "class_weight": "balanced",
            "solver": "lbfgs",
            "max_iter": 1000
        },
        "threshold_selection": {
            "locked_threshold": locked_threshold,
            "metric": "validation macro F1 with YES recall tie-breaker"
        }
    }

    config_path = os.path.join(OUTPUT_DIR, "tfidf_baseline_experiment_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print("\n[SUCCESS] Pipeline completed successfully. All artifacts generated in ml/")


if __name__ == "__main__":
    main()
