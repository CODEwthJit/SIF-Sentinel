"""
SIF Reconciliation Engine
Phase 7.2 — SIH26165

Combines independently generated Machine Learning (Phase 6.1 TF-IDF) predictions
and Rule-Based (V2.3 Frozen Engine) annotations into a categorical, auditable triage assessment.

Strict Architectural Principles:
1. No Numerical Weighting: Strictly forbids ad-hoc mathematical averaging
   (e.g., `final_score = x * ML + y * Rule` is explicitly prohibited).
2. Categorical Agreement Matrix: Surfaces agreement and disagreement as transparent states.
3. Review Triage: Assigns operational review priorities (HIGH / MEDIUM / LOW).
4. Metadata Quarantine: Rejects any attempt to pass outcome severity, hospitalization,
   or administrative codes into the reconciliation process.
5. Deterministic Semantics: Generates explainable audit rationales strictly from actual engine outputs.
"""

from typing import Dict, Any, Union, Optional


VALID_ML_LABELS = {"YES", "NO"}
VALID_RULE_LABELS = {"YES", "NO", "UNCERTAIN"}

PROHIBITED_METADATA_KEYS = {
    "source_dataset", "source_record_id", "source_secondary_id",
    "event_headline", "event_keywords", "hazard_stratum",
    "source_event_code", "source_event_title", "source_nature_title",
    "source_part_title", "source_equipment_source", "operational_context",
    "reference_outcome_context", "hospitalized", "amputation", "fatal",
    "candidate_stratum", "sampling_batch", "leak_prevention_cluster_id"
}

# Categorical Reconciliation States
STATUS_CONSENSUS_SIF = "CONSENSUS_SIF"
STATUS_CONSENSUS_NON_SIF = "CONSENSUS_NON_SIF"
STATUS_RULE_UNCERTAIN_ML_SIGNAL = "RULE_UNCERTAIN_ML_SIGNAL"
STATUS_RULE_UNCERTAIN_NO_ML_SIGNAL = "RULE_UNCERTAIN_NO_ML_SIGNAL"
STATUS_DIRECT_DISAGREEMENT = "DIRECT_DISAGREEMENT"

# Priority Levels
PRIORITY_HIGH = "HIGH"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_LOW = "LOW"


class SIFReconciliationEngine:
    """
    Decoupled reconciliation engine implementing the categorical agreement matrix.
    """

    def validate_payload(self, payload: Dict[str, Any]) -> None:
        """
        Validates the incoming reconciliation payload schema.
        Raises ValueError or TypeError if malformed or quarantined fields are present.
        """
        if not isinstance(payload, dict):
            raise TypeError(f"Payload must be a dict, got {type(payload).__name__}")

        # Check for quarantined metadata
        prohibited_present = set(payload.keys()).intersection(PROHIBITED_METADATA_KEYS)
        if prohibited_present:
            raise ValueError(
                f"Metadata quarantine violation: Prohibited keys detected in reconciliation payload: {sorted(list(prohibited_present))}. "
                "The reconciliation engine operates strictly on 'narrative', 'ml_result', and 'rule_result'."
            )

        # Required root keys
        for key in ["narrative", "ml_result", "rule_result"]:
            if key not in payload:
                raise ValueError(f"Missing required key in reconciliation payload: '{key}'")

        narrative = payload["narrative"]
        if not isinstance(narrative, str) or not narrative.strip():
            raise ValueError("Field 'narrative' must be a non-empty string.")

        ml_result = payload["ml_result"]
        if not isinstance(ml_result, dict):
            raise TypeError(f"Field 'ml_result' must be a dict, got {type(ml_result).__name__}")

        # Check for quarantined metadata in ml_result
        ml_prohibited = set(ml_result.keys()).intersection(PROHIBITED_METADATA_KEYS)
        if ml_prohibited:
            raise ValueError(
                f"Metadata quarantine violation: Prohibited keys detected in ml_result: {sorted(list(ml_prohibited))}."
            )

        # Validate ml_result schema
        ml_label = ml_result.get("ml_label") or ml_result.get("label")
        if ml_label not in VALID_ML_LABELS:
            raise ValueError(f"Invalid or missing 'ml_label' in ml_result: {ml_result.get('ml_label')}. Expected 'YES' or 'NO'.")

        if "ml_score" not in ml_result and "score" not in ml_result:
            raise ValueError("Missing 'ml_score' in ml_result.")

        raw_score = ml_result.get("ml_score") if "ml_score" in ml_result else ml_result.get("score")
        try:
            score = float(raw_score)
        except (ValueError, TypeError):
            raise ValueError(f"Field 'ml_score' must be a numeric float, got {raw_score}")

        if not (0.0 <= score <= 1.0):
            raise ValueError(f"Field 'ml_score' must be bounded in [0.0, 1.0], got {score}")

        rule_result = payload["rule_result"]
        if not isinstance(rule_result, dict):
            raise TypeError(f"Field 'rule_result' must be a dict, got {type(rule_result).__name__}")

        # Check for quarantined metadata in rule_result
        rule_prohibited = set(rule_result.keys()).intersection(PROHIBITED_METADATA_KEYS)
        if rule_prohibited:
            raise ValueError(
                f"Metadata quarantine violation: Prohibited keys detected in rule_result: {sorted(list(rule_prohibited))}."
            )

        # Validate rule_result schema
        rule_label = rule_result.get("sif_label") or rule_result.get("label")
        if rule_label not in VALID_RULE_LABELS:
            raise ValueError(f"Invalid or missing 'sif_label' in rule_result: {rule_result.get('sif_label')}. Expected 'YES', 'NO', or 'UNCERTAIN'.")

    def reconcile(
        self,
        narrative: Optional[str] = None,
        ml_result: Optional[Dict[str, Any]] = None,
        rule_result: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes the categorical reconciliation matrix against ML and Rule outputs.

        Can be called with individual arguments or a single payload dictionary.
        """
        if payload is not None:
            active_payload = payload
        else:
            active_payload = {
                "narrative": narrative,
                "ml_result": ml_result,
                "rule_result": rule_result
            }

        self.validate_payload(active_payload)

        ml_res = active_payload["ml_result"]
        rule_res = active_payload["rule_result"]

        ml_label = ml_res.get("ml_label") or ml_res.get("label")
        raw_score = ml_res.get("ml_score") if "ml_score" in ml_res else ml_res.get("score")
        ml_score = float(raw_score)
        threshold = float(ml_res.get("threshold", 0.59))

        rule_label = rule_res.get("sif_label") or rule_res.get("label")
        reason_code = rule_res.get("reason_code") or rule_res.get("reason_code_v23") or "UNKNOWN"
        energy = rule_res.get("controlling_hazard_energy") or rule_res.get("controlling_hazard_energy_v23") or rule_res.get("energy") or "UNKNOWN"

        # ---------------------------------------------------------------------
        # Categorical Reconciliation Matrix (Zero Magic Formulas)
        # ---------------------------------------------------------------------
        if ml_label == "YES" and rule_label == "YES":
            status = STATUS_CONSENSUS_SIF
            priority = PRIORITY_HIGH
            discrepancy = False
            review_required = False
            explanation = (
                f"Full Consensus SIF Precursor: ML predicts YES (score={ml_score:.4f}) and V2.3 rule engine predicts YES "
                f"(energy={energy}, reason={reason_code}). High-confidence precursor candidate."
            )

        elif ml_label == "NO" and rule_label == "NO":
            status = STATUS_CONSENSUS_NON_SIF
            priority = PRIORITY_LOW
            discrepancy = False
            review_required = False
            explanation = (
                f"Full Consensus Non-SIF: ML predicts NO (score={ml_score:.4f}) and V2.3 rule engine predicts NO "
                f"(reason={reason_code}). Routine, low-energy, or natural medical incident."
            )

        elif ml_label == "YES" and rule_label == "UNCERTAIN":
            status = STATUS_RULE_UNCERTAIN_ML_SIGNAL
            priority = PRIORITY_HIGH
            discrepancy = True
            review_required = True
            explanation = (
                f"Rule Engine Uncertain with Strong ML Signal: ML predicts YES (score={ml_score:.4f} >= threshold {threshold:.2f}) "
                f"while V2.3 rule engine is UNCERTAIN (reason={reason_code}). Narrative exhibits statistical precursor vocabulary "
                "but lacks explicit syntactic proof. Gated for human safety review."
            )

        elif ml_label == "NO" and rule_label == "UNCERTAIN":
            status = STATUS_RULE_UNCERTAIN_NO_ML_SIGNAL
            priority = PRIORITY_MEDIUM
            discrepancy = True
            review_required = True
            explanation = (
                f"Rule Engine Uncertain with No ML Signal: ML predicts NO (score={ml_score:.4f} < threshold {threshold:.2f}) "
                f"and V2.3 rule engine is UNCERTAIN (reason={reason_code}). Incident lacks both deterministic and statistical "
                "precursor markers. Moderate review priority."
            )

        elif (ml_label == "YES" and rule_label == "NO") or (ml_label == "NO" and rule_label == "YES"):
            status = STATUS_DIRECT_DISAGREEMENT
            priority = PRIORITY_HIGH
            discrepancy = True
            review_required = True
            if ml_label == "YES" and rule_label == "NO":
                explanation = (
                    f"Direct Domain Disagreement: ML predicts YES (score={ml_score:.4f}) while V2.3 rule engine predicts NO "
                    f"(reason={reason_code}). Potential edge-case or industrial vocabulary false positive. "
                    "Must NOT be automatically averaged or overridden; human safety audit required."
                )
            else:
                explanation = (
                    f"Direct Domain Disagreement: ML predicts NO (score={ml_score:.4f}) while V2.3 rule engine predicts YES "
                    f"(energy={energy}, reason={reason_code}). Deterministic rule fired despite low ML score. "
                    "Must NOT be automatically averaged or overridden; human safety audit required."
                )
        else:
            raise ValueError(f"Unhandled label combination: ML={ml_label}, Rule={rule_label}")

        return {
            "reconciliation_status": status,
            "review_priority": priority,
            "status": status,
            "priority": priority,
            "ml_result": ml_res,
            "rule_result": rule_res,
            "discrepancy_flag": discrepancy,
            "discrepancy": discrepancy,
            "review_required": review_required,
            "explanation": explanation
        }


# Convenience singleton
_RECONCILIATION_ENGINE = SIFReconciliationEngine()

def reconcile_sif_evidence(
    narrative: str,
    ml_result: Dict[str, Any],
    rule_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Module-level convenience wrapper for SIF evidence reconciliation.
    """
    return _RECONCILIATION_ENGINE.reconcile(
        narrative=narrative,
        ml_result=ml_result,
        rule_result=rule_result
    )
