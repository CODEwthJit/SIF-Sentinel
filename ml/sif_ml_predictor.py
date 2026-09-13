"""
SIF ML Predictor Module
Phase 7.1 — SIH26165

Official, frozen inference interface for the Phase 6.1 TF-IDF + Logistic Regression
baseline model for SIF Precursor Detection.

Strict Design Principles:
1. Pure Narrative Input: Accepts strictly `normalized_narrative`.
2. Metadata Quarantine: Rejects any attempt to feed structured metadata or outcome fields.
3. Deterministic & Frozen: Uses locked Phase 6.1 weights (C=100.0, tau=0.59).
4. Lexical Explainability: Computes exact feature-level log-odds contributions (w_j * x_j)
   for tokens and bigrams that actually appear in the input narrative.
5. Decision Semantics: ml_score represents the model-estimated likelihood of the YES class
   under the provisional V2.3 automated framework, NOT probability of death or injury.
"""

import os
import re
from typing import Dict, Any, List, Union, Optional
import joblib
import numpy as np
import scipy.sparse


DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "tfidf_baseline_model.joblib")
DEFAULT_VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "tfidf_baseline_vectorizer.joblib")
LOCKED_THRESHOLD = 0.59

DISALLOWED_METADATA_KEYS = {
    "source_dataset", "source_record_id", "source_secondary_id",
    "event_headline", "event_keywords", "hazard_stratum",
    "source_event_code", "source_event_title", "source_nature_title",
    "source_part_title", "source_equipment_source", "operational_context",
    "reference_outcome_context", "hospitalized", "amputation", "fatal",
    "hazard_energy", "activity", "barrier_control", "barrier_failure",
    "human_exposure", "potential_consequence", "lsr_tags", "reason_code",
    "sif_label", "sif_label_v2", "sif_label_v23", "candidate_stratum",
    "sampling_batch", "leak_prevention_cluster_id"
}


class SIFMLPredictor:
    """
    Inference engine for SIF precursor detection using the frozen Phase 6.1 model.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        vectorizer_path: Optional[str] = None,
        threshold: float = LOCKED_THRESHOLD
    ):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.vectorizer_path = vectorizer_path or DEFAULT_VECTORIZER_PATH
        self.threshold = float(threshold)

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")
        if not os.path.exists(self.vectorizer_path):
            raise FileNotFoundError(f"Vectorizer file not found at: {self.vectorizer_path}")

        self.model = joblib.load(self.model_path)
        self.vectorizer = joblib.load(self.vectorizer_path)
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())
        self.coefficients = self.model.coef_[0]
        self.intercept = float(self.model.intercept_[0])

    def _validate_input(self, input_data: Union[str, Dict[str, Any]]) -> str:
        """
        Validates input and strictly enforces metadata quarantine.
        """
        if isinstance(input_data, str):
            text = input_data.strip()
            if not text:
                raise ValueError("Input narrative text must not be empty.")
            return text

        if isinstance(input_data, dict):
            # Strict feature quarantine: Only 'normalized_narrative' is permitted
            allowed_keys = {"normalized_narrative"}
            extra_keys = set(input_data.keys()) - allowed_keys
            if extra_keys:
                raise ValueError(
                    f"Metadata quarantine violation: Prohibited metadata keys detected in input: {sorted(list(extra_keys))}. "
                    "The ML model accepts strictly 'normalized_narrative' and cannot ingest outcome, administrative, or ontology fields."
                )

            if "normalized_narrative" in input_data:
                text = str(input_data["normalized_narrative"]).strip()
                if not text:
                    raise ValueError("Field 'normalized_narrative' must not be empty.")
                return text

            raise ValueError("Input dictionary must contain the 'normalized_narrative' key.")

        raise TypeError(f"Expected str or dict, got {type(input_data).__name__}")

    def predict(
        self,
        input_data: Union[str, Dict[str, Any]],
        top_k_evidence: int = 5
    ) -> Dict[str, Any]:
        """
        Runs inference on a single incident narrative.

        Args:
            input_data: Incident narrative string or dict containing 'normalized_narrative'.
            top_k_evidence: Number of top positive and negative contributing n-grams to return.

        Returns:
            Dict containing:
                ml_label: "YES" if ml_score >= threshold else "NO"
                ml_score: float in [0.0, 1.0] (probability of SIF precursor under V2.3)
                threshold: float decision boundary (0.59)
                positive_evidence: list of dicts of top n-grams pushing score higher
                negative_evidence: list of dicts of top n-grams pulling score lower
                decision_rationale: brief textual summary
        """
        narrative = self._validate_input(input_data)

        # Vectorize using frozen training vocabulary
        X = self.vectorizer.transform([narrative])

        # Generate class probabilities
        probs = self.model.predict_proba(X)[0]
        # Probability of class 1 (YES)
        ml_score = float(probs[1])
        ml_label = "YES" if ml_score >= self.threshold else "NO"

        # Explainability: Feature-level contribution = x_j * w_j
        # Only evaluate non-zero features that ACTUALLY occur in the input
        nz_indices = X.nonzero()[1]
        contributions = []

        for idx in nz_indices:
            val = float(X[0, idx])
            weight = float(self.coefficients[idx])
            contrib = val * weight
            contributions.append({
                "feature": str(self.feature_names[idx]),
                "contribution": round(contrib, 4),
                "tfidf_value": round(val, 4),
                "weight": round(weight, 4)
            })

        pos_evidence = sorted([c for c in contributions if c["contribution"] > 0],
                              key=lambda x: x["contribution"], reverse=True)[:top_k_evidence]
        neg_evidence = sorted([c for c in contributions if c["contribution"] < 0],
                              key=lambda x: x["contribution"])[:top_k_evidence]

        # Build transparent rationale
        if ml_label == "YES":
            top_pos_str = ", ".join([f"'{e['feature']}' (+{e['contribution']:.2f})" for e in pos_evidence[:3]])
            rationale = f"Score {ml_score:.4f} >= threshold {self.threshold:.2f}. Dominant SIF evidence: {top_pos_str or 'general vocabulary'}."
        else:
            top_neg_str = ", ".join([f"'{e['feature']}' ({e['contribution']:.2f})" for e in neg_evidence[:3]])
            rationale = f"Score {ml_score:.4f} < threshold {self.threshold:.2f}. Mitigating/routine evidence: {top_neg_str or 'lack of positive SIF signals'}."

        return {
            "ml_label": ml_label,
            "ml_score": round(ml_score, 4),
            "threshold": self.threshold,
            "positive_evidence": pos_evidence,
            "negative_evidence": neg_evidence,
            "decision_rationale": rationale
        }

    def batch_predict(
        self,
        narratives: List[Union[str, Dict[str, Any]]],
        top_k_evidence: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Runs inference on a list of incident narratives.
        """
        return [self.predict(n, top_k_evidence=top_k_evidence) for n in narratives]


# Module-level convenience function
_GLOBAL_PREDICTOR: Optional[SIFMLPredictor] = None

def predict_sif_precursor(
    narrative: Union[str, Dict[str, Any]],
    threshold: float = LOCKED_THRESHOLD
) -> Dict[str, Any]:
    """
    Convenience function for standalone single-narrative inference.
    """
    global _GLOBAL_PREDICTOR
    if _GLOBAL_PREDICTOR is None or _GLOBAL_PREDICTOR.threshold != threshold:
        _GLOBAL_PREDICTOR = SIFMLPredictor(threshold=threshold)
    return _GLOBAL_PREDICTOR.predict(narrative)
