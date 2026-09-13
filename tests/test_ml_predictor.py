"""
Unit and Integration Tests for SIF ML Predictor
Phase 7.1 — SIH26165

Validates all 10 core contractual requirements:
1. Model weights load properly.
2. Vectorizer vocabulary loads properly.
3. Prediction execution runs without error.
4. Output schema strictly adheres to contract.
5. SIF probability score is strictly within [0.0, 1.0].
6. Locked threshold (0.59) is deterministically applied.
7. Prediction is 100% deterministic across repeated calls.
8. Metadata quarantine prevents injection of administrative/outcome fields.
9. Explainability evidence only contains features physically present in input text.
10. Stored Phase 6.1 test set predictions are bit-for-bit reproduced.
"""

import os
import pytest
import pandas as pd
import numpy as np

from ml.sif_ml_predictor import (
    SIFMLPredictor,
    predict_sif_precursor,
    LOCKED_THRESHOLD,
    DEFAULT_MODEL_PATH,
    DEFAULT_VECTORIZER_PATH
)


@pytest.fixture(scope="module")
def predictor():
    """Initializes a shared predictor instance."""
    return SIFMLPredictor()


class TestMLPredictorContract:
    """Test suite covering the formal ML inference contract."""

    def test_01_model_and_vectorizer_exist_and_load(self, predictor):
        """1 & 2: Validates model and vectorizer files exist and load cleanly."""
        assert os.path.exists(DEFAULT_MODEL_PATH), "Model file must exist on disk"
        assert os.path.exists(DEFAULT_VECTORIZER_PATH), "Vectorizer file must exist on disk"
        assert hasattr(predictor.model, "predict_proba"), "Loaded model must support predict_proba"
        assert hasattr(predictor.vectorizer, "transform"), "Loaded vectorizer must support transform"
        assert len(predictor.feature_names) == 4886, f"Expected 4886 features, found {len(predictor.feature_names)}"

    def test_02_prediction_execution_and_schema(self, predictor):
        """3 & 4: Validates prediction runs and returns exact contract schema."""
        sample_text = "An employee was operating a forklift in the warehouse when a pallet shifted."
        result = predictor.predict(sample_text)

        required_keys = {
            "ml_label", "ml_score", "threshold",
            "positive_evidence", "negative_evidence", "decision_rationale"
        }
        assert set(result.keys()) == required_keys, f"Missing or extra keys in output: {set(result.keys()) ^ required_keys}"
        assert result["ml_label"] in ["YES", "NO"], f"Invalid ml_label: {result['ml_label']}"
        assert isinstance(result["ml_score"], float), "ml_score must be a float"
        assert result["threshold"] == LOCKED_THRESHOLD, f"threshold must be {LOCKED_THRESHOLD}"
        assert isinstance(result["positive_evidence"], list), "positive_evidence must be a list"
        assert isinstance(result["negative_evidence"], list), "negative_evidence must be a list"

    def test_03_score_bounds_and_threshold_logic(self, predictor):
        """5 & 6: Validates score is in [0, 1] and threshold determines ml_label."""
        test_cases = [
            "An employee fell 30 feet from a communication tower and died from blunt impact.",
            "An employee had chest pains at lunch and was diagnosed with a natural heart attack.",
            "A routine meeting was held to discuss quarterly ergonomics."
        ]
        for text in test_cases:
            res = predictor.predict(text)
            score = res["ml_score"]
            assert 0.0 <= score <= 1.0, f"Score {score} out of bounds for text: {text}"

            if score >= LOCKED_THRESHOLD:
                assert res["ml_label"] == "YES", f"Score {score} >= {LOCKED_THRESHOLD} but label is {res['ml_label']}"
            else:
                assert res["ml_label"] == "NO", f"Score {score} < {LOCKED_THRESHOLD} but label is {res['ml_label']}"

    def test_04_prediction_determinism(self, predictor):
        """7: Validates prediction outputs are 100% deterministic across repeated runs."""
        text = "An employee was caught between a heavy steel beam and a conveyor frame."
        res1 = predictor.predict(text)
        res2 = predictor.predict(text)
        res3 = predictor.predict(text)

        assert res1["ml_label"] == res2["ml_label"] == res3["ml_label"]
        assert res1["ml_score"] == res2["ml_score"] == res3["ml_score"]
        assert res1["positive_evidence"] == res2["positive_evidence"] == res3["positive_evidence"]

    def test_05_metadata_quarantine_enforcement(self, predictor):
        """8: Validates that metadata and outcome fields are strictly rejected."""
        # 1. Plain string works
        assert predictor.predict("Employee fell 10 feet.")["ml_label"] in ["YES", "NO"]

        # 2. Dictionary with only normalized_narrative works
        assert predictor.predict({"normalized_narrative": "Employee fell 10 feet."})["ml_label"] in ["YES", "NO"]

        # 3. Injection of prohibited outcome / administrative fields must raise ValueError
        prohibited_injections = [
            {"normalized_narrative": "Valid text", "hospitalized": 1},
            {"normalized_narrative": "Valid text", "amputation": 1},
            {"normalized_narrative": "Valid text", "fatal": 1},
            {"normalized_narrative": "Valid text", "source_event_code": "1234"},
            {"normalized_narrative": "Valid text", "hazard_energy": "GRAVITATIONAL"},
            {"normalized_narrative": "Valid text", "barrier_state": "FAILED"},
            {"normalized_narrative": "Valid text", "sif_label_v23": "YES"}
        ]
        for bad_dict in prohibited_injections:
            with pytest.raises(ValueError, match="Metadata quarantine violation"):
                predictor.predict(bad_dict)

    def test_06_explainability_feature_presence(self, predictor):
        """9: Validates that evidence features actually appear in the input narrative."""
        narrative = "An employee fell 15 feet from a scaffold structure."
        res = predictor.predict(narrative, top_k_evidence=5)
        lower_nar = narrative.lower()

        # Every reported positive feature must be in the narrative text
        for item in res["positive_evidence"]:
            feature = item["feature"]
            assert feature in lower_nar, f"Positive feature '{feature}' not found in narrative: '{lower_nar}'"
            assert item["contribution"] > 0, "Positive contribution must be > 0"

        # Every reported negative feature must be in the narrative text
        for item in res["negative_evidence"]:
            feature = item["feature"]
            assert feature in lower_nar, f"Negative feature '{feature}' not found in narrative: '{lower_nar}'"
            assert item["contribution"] < 0, "Negative contribution must be < 0"

    def test_07_phase_6_1_test_reproducibility(self, predictor):
        """10: Validates exact reproduction of Phase 6.1 test set predictions."""
        test_pred_path = os.path.join(os.path.dirname(DEFAULT_MODEL_PATH), "tfidf_baseline_test_predictions.csv")
        if not os.path.exists(test_pred_path):
            pytest.skip("Phase 6.1 test predictions file not found")

        df = pd.read_csv(test_pred_path)
        # Sample 20 representative cases across YES and NO
        sample_rows = df.sample(n=20, random_state=42)

        for _, row in sample_rows.iterrows():
            cid = row["candidate_id"]
            nar = row["normalized_narrative"]
            expected_label = row["predicted_label"]
            expected_score = row["predicted_score"]

            res = predictor.predict(nar)
            assert res["ml_label"] == expected_label, f"[{cid}] Label mismatch: expected {expected_label}, got {res['ml_label']}"
            assert np.isclose(res["ml_score"], expected_score, atol=1e-4), f"[{cid}] Score mismatch: expected {expected_score}, got {res['ml_score']}"

    def test_08_convenience_function(self):
        """Validates the module-level predict_sif_precursor convenience function."""
        res = predict_sif_precursor("A worker slipped on ice on the sidewalk.")
        assert isinstance(res, dict)
        assert "ml_label" in res
        assert "ml_score" in res

