import React from 'react';
import { Cpu, TrendingUp, TrendingDown, Info } from 'lucide-react';
import { MLEvidence } from '../types/api';

interface MLEvidenceCardProps {
  ml: MLEvidence;
}

export const MLEvidenceCard: React.FC<MLEvidenceCardProps> = ({ ml }) => {
  const isYes = ml.label === 'YES';

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-50 text-sky-700">
            <Cpu className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">Machine Learning Evidence</h3>
            <p className="text-xs text-slate-500">TF-IDF + Logistic Regression Baseline (Locked)</p>
          </div>
        </div>
        <span
          className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-bold font-mono ${
            isYes ? 'bg-red-100 text-red-800' : 'bg-slate-100 text-slate-700'
          }`}
        >
          PREDICTION: {ml.label}
        </span>
      </div>

      {/* Metrics Row */}
      <div className="mt-5 grid grid-cols-2 gap-4 rounded-lg bg-slate-50 p-3.5 text-center">
        <div>
          <span className="text-xs text-slate-500 uppercase tracking-wider">Model Propensity</span>
          <div className="mt-1 font-mono text-2xl font-bold text-slate-900">{ml.score.toFixed(4)}</div>
        </div>
        <div className="border-l border-slate-200">
          <span className="text-xs text-slate-500 uppercase tracking-wider">Decision Threshold</span>
          <div className="mt-1 font-mono text-2xl font-bold text-slate-600">τ = {ml.threshold.toFixed(2)}</div>
        </div>
      </div>

      {/* Mandatory Scientific Caption */}
      <div className="mt-3 flex items-start gap-1.5 text-xs text-slate-500">
        <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5 text-sky-600" />
        <span>
          <strong>Model-estimated SIF precursor propensity</strong> under provisional V2.3 labels. Not a physical probability of death or injury.
        </span>
      </div>

      {/* Rationale */}
      {ml.decision_rationale && (
        <div className="mt-4 rounded border border-slate-200 bg-white p-3 text-xs text-slate-700">
          <strong className="text-slate-900">Rationale:</strong> {ml.decision_rationale}
        </div>
      )}

      {/* Lexical Evidence Tables */}
      <div className="mt-5 space-y-4">
        {ml.positive_evidence && ml.positive_evidence.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-red-700 mb-2">
              <TrendingUp className="h-3.5 w-3.5" />
              <span>Positive Contributing Features (+ SIF Propensity)</span>
            </div>
            <div className="overflow-hidden rounded-lg border border-slate-200 text-xs">
              <table className="w-full text-left">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 font-medium">
                  <tr>
                    <th className="py-2 px-3">Token / Feature</th>
                    <th className="py-2 px-3 text-right">Contribution (x_j · w_j)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {ml.positive_evidence.slice(0, 5).map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="py-1.5 px-3 font-sans font-medium text-slate-800">{item.feature}</td>
                      <td className="py-1.5 px-3 text-right text-red-700 font-semibold">
                        +{item.contribution.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {ml.negative_evidence && ml.negative_evidence.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 mb-2">
              <TrendingDown className="h-3.5 w-3.5" />
              <span>Mitigating / Routine Features (- SIF Propensity)</span>
            </div>
            <div className="overflow-hidden rounded-lg border border-slate-200 text-xs">
              <table className="w-full text-left">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-200 font-medium">
                  <tr>
                    <th className="py-2 px-3">Token / Feature</th>
                    <th className="py-2 px-3 text-right">Contribution (x_j · w_j)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {ml.negative_evidence.slice(0, 5).map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="py-1.5 px-3 font-sans font-medium text-slate-800">{item.feature}</td>
                      <td className="py-1.5 px-3 text-right text-emerald-700 font-semibold">
                        {item.contribution.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

