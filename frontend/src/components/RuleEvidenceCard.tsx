import React from 'react';
import { ShieldCheck, Flame, Layers, UserCheck, CheckCircle2 } from 'lucide-react';
import { RuleEvidence } from '../types/api';

interface RuleEvidenceCardProps {
  rule: RuleEvidence;
}

export const RuleEvidenceCard: React.FC<RuleEvidenceCardProps> = ({ rule }) => {
  const isYes = rule.label === 'YES';
  const isUncertain = rule.label === 'UNCERTAIN';

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
            <ShieldCheck className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">V2.3 Deterministic Rule Engine</h3>
            <p className="text-xs text-slate-500">Narrative Physics & Energy Precedence Deduction</p>
          </div>
        </div>
        <span
          className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-bold font-mono ${
            isYes
              ? 'bg-red-100 text-red-800'
              : isUncertain
              ? 'bg-amber-100 text-amber-800'
              : 'bg-emerald-100 text-emerald-800'
          }`}
        >
          RULE LABEL: {rule.label}
        </span>
      </div>

      {/* Structured Deductions Table */}
      <div className="mt-5 divide-y divide-slate-100 rounded-lg border border-slate-200 text-xs">
        <div className="flex items-center justify-between p-3 bg-slate-50">
          <span className="flex items-center gap-2 text-slate-600 font-medium">
            <Flame className="h-3.5 w-3.5 text-amber-600" />
            Controlling Hazard Energy
          </span>
          <span className="font-mono font-bold text-slate-900">
            {rule.controlling_hazard_energy || 'Not available'}
          </span>
        </div>

        <div className="flex items-center justify-between p-3">
          <span className="text-slate-600 font-medium">Reason Taxonomy Code</span>
          <span className="font-mono font-semibold text-slate-800">
            {rule.reason_code || 'Not available'}
          </span>
        </div>

        <div className="flex items-center justify-between p-3 bg-slate-50">
          <span className="flex items-center gap-2 text-slate-600 font-medium">
            <Layers className="h-3.5 w-3.5 text-sky-600" />
            Barrier State
          </span>
          <span className="font-mono text-slate-800">
            {rule.barrier_state || 'Not available'}
          </span>
        </div>

        <div className="flex items-center justify-between p-3">
          <span className="flex items-center gap-2 text-slate-600 font-medium">
            <UserCheck className="h-3.5 w-3.5 text-indigo-600" />
            Human Exposure
          </span>
          <span className="font-mono text-slate-800">
            {rule.human_exposure || 'Not available'}
          </span>
        </div>

        <div className="flex items-center justify-between p-3 bg-slate-50">
          <span className="flex items-center gap-2 text-slate-600 font-medium">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
            Evidence Sufficiency
          </span>
          <span className="font-mono text-slate-800">
            {rule.evidence_sufficiency || 'Not available'}
          </span>
        </div>

        {rule.precursor_type && (
          <div className="flex items-center justify-between p-3">
            <span className="text-slate-600 font-medium">Precursor Type</span>
            <span className="font-mono text-slate-800">
              {rule.precursor_type}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

