/**
 * TypeScript Definitions for SIH26165 Backend API Contracts
 * Mirrors backend Pydantic schemas accurately.
 */

export interface ReportOut {
  id: number;
  narrative: string;
  created_at: string;
}

export interface ReportCreate {
  narrative: string;
}

export interface LexicalEvidenceItem {
  feature: string;
  contribution: number;
  tfidf_value?: number | null;
  weight?: number | null;
}

export interface MLEvidence {
  label: 'YES' | 'NO' | string;
  score: number;
  threshold: number;
  positive_evidence: LexicalEvidenceItem[];
  negative_evidence: LexicalEvidenceItem[];
  decision_rationale?: string | null;
}

export interface RuleEvidence {
  label: 'YES' | 'NO' | 'UNCERTAIN' | string;
  reason_code?: string | null;
  controlling_hazard_energy?: string | null;
  barrier_state?: string | null;
  human_exposure?: string | null;
  evidence_sufficiency?: string | null;
  precursor_type?: string | null;
  confidence?: string | null;
}

export interface Reconciliation {
  status: 'CONSENSUS_SIF' | 'CONSENSUS_NON_SIF' | 'RULE_UNCERTAIN_ML_SIGNAL' | 'RULE_UNCERTAIN_NO_ML_SIGNAL' | 'DIRECT_DISAGREEMENT' | string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  discrepancy: boolean;
  review_required: boolean;
  explanation?: string | null;
}

export interface AnalysisResponse {
  report: ReportOut;
  ml: MLEvidence;
  rule: RuleEvidence;
  reconciliation: Reconciliation;
}

export interface ReportDetailResponse {
  report: ReportOut;
  latest_analysis?: AnalysisResponse | null;
  total_analyses: number;
}

export interface DashboardStats {
  total_reports: number;
  total_analyses: number;
  consensus_sif_count: number;
  consensus_non_sif_count: number;
  discrepancy_count: number;
  high_priority_count: number;
  medium_priority_count: number;
  low_priority_count: number;
  reconciliation_status_distribution: Record<string, number>;
  review_priority_distribution: Record<string, number>;
  rule_reason_code_distribution: Record<string, number>;
  hazard_energy_distribution: Record<string, number>;
}

export interface RecentAnalysisItem {
  report_id: number;
  narrative_preview: string;
  ml_label: string;
  ml_score: number;
  rule_label: string;
  reconciliation_status: string;
  review_priority: string;
  human_review_required: boolean;
  created_at: string;
}

export interface DashboardRecent {
  total_returned: number;
  recent_analyses: RecentAnalysisItem[];
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  pipeline: string;
  ml_model: string;
  reconciliation: string;
}

