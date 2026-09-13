import React from 'react';
import { GitCompare, AlertTriangle, CheckCircle2, AlertOctagon } from 'lucide-react';
import { Reconciliation } from '../types/api';
import { StatusBadge } from './StatusBadge';
import { PriorityBadge } from './PriorityBadge';

interface ReconciliationCardProps {
  reconciliation: Reconciliation;
}

export const ReconciliationCard: React.FC<ReconciliationCardProps> = ({ reconciliation }) => {
  const isDisagreement = reconciliation.status === 'DIRECT_DISAGREEMENT';
  const isReviewRequired = reconciliation.review_required;

  return (
    <div
      className={`rounded-xl border p-6 shadow-sm transition-all ${
        isDisagreement
          ? 'border-purple-300 bg-purple-50/40'
          : isReviewRequired
          ? 'border-amber-300 bg-amber-50/30'
          : 'border-slate-200 bg-white'
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 pb-4">
        <div className="flex items-center gap-2.5">
          <div
            className={`flex h-8 w-8 items-center justify-center rounded-lg ${
              isDisagreement
                ? 'bg-purple-100 text-purple-800'
                : 'bg-indigo-50 text-indigo-700'
            }`}
          >
            <GitCompare className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
              SIF Reconciliation & Triage Assessment
            </h3>
            <p className="text-xs text-slate-500">Categorical Agreement Matrix (Zero Weighted Formulas)</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <StatusBadge status={reconciliation.status} size="md" />
          <PriorityBadge priority={reconciliation.priority} size="md" />
        </div>
      </div>

      {/* Prominent Disagreement Warning Callout */}
      {isDisagreement && (
        <div className="mt-4 flex items-start gap-3 rounded-lg border-2 border-purple-400 bg-purple-100 p-4 text-purple-950 shadow-sm">
          <AlertOctagon className="h-6 w-6 flex-shrink-0 text-purple-700 mt-0.5" />
          <div className="text-xs">
            <h4 className="font-bold text-sm text-purple-900 uppercase tracking-wide">
              Model and rule engine disagree — human review required.
            </h4>
            <p className="mt-1 font-medium text-purple-950">
              The statistical ML model and deterministic V2.3 rule engine produced conflicting SIF precursor assessments. This incident is prioritized for mandatory human safety audit.
            </p>
          </div>
        </div>
      )}

      {/* Consensus SIF Callout */}
      {reconciliation.status === 'CONSENSUS_SIF' && (
        <div className="mt-4 flex items-start gap-3 rounded-lg border border-red-300 bg-red-50 p-4 text-red-950">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 text-red-600 mt-0.5" />
          <div className="text-xs">
            <h4 className="font-bold text-red-900 uppercase tracking-wide">
              Consensus SIF Precursor Confirmed ({reconciliation.priority} Priority)
            </h4>
            <p className="mt-1 text-red-900">
              Both the machine learning model and deterministic rule engine independently confirm high-energy SIF precursor characteristics.
            </p>
          </div>
        </div>
      )}

      {/* Consensus Non-SIF Callout */}
      {reconciliation.status === 'CONSENSUS_NON_SIF' && (
        <div className="mt-4 flex items-start gap-3 rounded-lg border border-emerald-300 bg-emerald-50 p-4 text-emerald-950">
          <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-emerald-600 mt-0.5" />
          <div className="text-xs">
            <h4 className="font-bold text-emerald-900 uppercase tracking-wide">
              Consensus Non-SIF Confirmed
            </h4>
            <p className="mt-1 text-emerald-900">
              Both independent evidence channels agree on non-SIF classification: neither high-energy hazard exposure nor statistical SIF propensity was detected.
            </p>
          </div>
        </div>
      )}

      {/* Rule Uncertain Callouts */}
      {(reconciliation.status === 'RULE_UNCERTAIN_ML_SIGNAL' ||
        reconciliation.status === 'RULE_UNCERTAIN_NO_ML_SIGNAL') && (
        <div className="mt-4 flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-950">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 text-amber-600 mt-0.5" />
          <div className="text-xs">
            <h4 className="font-bold text-amber-900 uppercase tracking-wide">
              Human Review Required — Rule Evidence Uncertain
            </h4>
            <p className="mt-1 text-amber-900">
              {reconciliation.status === 'RULE_UNCERTAIN_ML_SIGNAL'
                ? 'Deterministic rule evidence is incomplete or ambiguous, while the ML model detected potential SIF lexical patterns. Human safety audit is required.'
                : 'Deterministic rule evidence is insufficient to verify SIF status, and the ML model detected no high-confidence signal. Safety professional review is recommended.'}
            </p>
          </div>
        </div>
      )}

      {/* Deterministic Explanation */}
      {reconciliation.explanation && (
        <div className="mt-4 rounded-lg bg-slate-50 border border-slate-200 p-4 text-xs text-slate-800 leading-relaxed font-sans">
          <strong className="text-slate-900 uppercase font-mono tracking-wider block mb-1">
            Reconciliation Audit Rationale
          </strong>
          {reconciliation.explanation}
        </div>
      )}

      {/* Flags Footer */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-slate-600 border-t border-slate-100 pt-3">
        <span>
          Discrepancy Flag: <strong className="font-mono">{reconciliation.discrepancy ? 'TRUE' : 'FALSE'}</strong>
        </span>
        <span>•</span>
        <span>
          Human Review Required:{' '}
          <strong className="font-mono">{reconciliation.review_required ? 'YES' : 'NO'}</strong>
        </span>
      </div>
    </div>
  );
};

