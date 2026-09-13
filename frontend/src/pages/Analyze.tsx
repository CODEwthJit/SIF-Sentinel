import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Send, FileText, Sparkles, AlertCircle, ArrowRight, ShieldAlert, CheckCircle2, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';
import { reportService } from '../services/reportService';
import { AnalysisResponse } from '../types/api';
import { MLEvidenceCard } from '../components/MLEvidenceCard';
import { RuleEvidenceCard } from '../components/RuleEvidenceCard';
import { ReconciliationCard } from '../components/ReconciliationCard';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

interface DemoExample {
  title: string;
  category: string;
  text: string;
}

const DEMO_EXAMPLES: DemoExample[] = [
  {
    title: 'Scaffold Fall',
    category: 'High-Energy Fall',
    text: 'A worker was working on a scaffold approximately 28 feet above ground when he fell from the scaffold to the ground.',
  },
  {
    title: 'Same-Level Slip',
    category: 'Low-Energy Event',
    text: 'An employee slipped and fell on ice on the sidewalk outside the entrance, bruising his knee.',
  },
  {
    title: 'Medical Event',
    category: 'Non-Precursor',
    text: 'An employee was seated in the conference room and suffered a fatal cardiac arrest.',
  },
  {
    title: 'Conveyor / Tool Jam',
    category: 'Domain Disagreement',
    text: 'An employee was using a wrench to remove snow that was blocking the magic carpet conveyor belt machine. As soon as the snow was released, the conveyor started going again and grabbed the wrench. When the employee tried to grab the tool, she was trapped under the conveyor belt bar, breaking her right humerus.',
  },
  {
    title: 'Ambiguous Incident',
    category: 'Uncertain Evidence',
    text: 'Worker was injured on site during normal shift operations.',
  },
];

export const Analyze: React.FC = () => {
  const [narrative, setNarrative] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [showExamples, setShowExamples] = useState(false);

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (loading) return; // Prevent duplicate requests

    setValidationError(null);
    setError(null);

    const clean = narrative.trim();
    if (!clean) {
      setValidationError('Narrative cannot be empty or whitespace-only. Please enter a safety report narrative.');
      return;
    }

    if (clean.length < 10) {
      setValidationError('Narrative is too short to evaluate SIF precursor mechanisms (minimum 10 characters required).');
      return;
    }

    setLoading(true);
    try {
      const data = await reportService.analyzeReport(clean);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Analysis pipeline execution failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyExample = (text: string) => {
    setNarrative(text);
    setValidationError(null);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Analyze Safety Report</h1>
        <p className="text-xs text-slate-500 mt-1">
          Evaluate an incident narrative for potential Serious Injury &amp; Fatality precursors.
        </p>
      </div>

      {/* Input Section */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
        {/* Expandable Demo Examples Accordion */}
        <div className="border border-slate-200 rounded-lg p-3 bg-slate-50/60">
          <button
            type="button"
            onClick={() => setShowExamples(!showExamples)}
            className="w-full flex items-center justify-between text-xs font-semibold text-slate-700 hover:text-sky-700 transition"
          >
            <span className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-sky-600" />
              <span>Try an example incident narrative</span>
              <span className="text-[10px] text-slate-400 font-normal ml-1">(Demonstration presets)</span>
            </span>
            {showExamples ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {showExamples && (
            <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {DEMO_EXAMPLES.map((ex, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleApplyExample(ex.text)}
                  className="rounded-lg border border-slate-200 bg-white p-2.5 text-left hover:border-sky-400 hover:bg-sky-50/50 transition group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800 group-hover:text-sky-800">{ex.title}</span>
                    <span className="text-[9px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                      {ex.category}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">{ex.text}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Narrative Form */}
        <form onSubmit={handleAnalyze} className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="narrative" className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                Report Narrative
              </label>
              <span className="text-[11px] text-slate-400 font-mono">{narrative.length} characters</span>
            </div>
            <textarea
              id="narrative"
              rows={5}
              value={narrative}
              onChange={(e) => {
                setNarrative(e.target.value);
                if (validationError) setValidationError(null);
              }}
              placeholder="Describe the incident narrative, equipment involved, worker positioning, and physical energies observed..."
              className="w-full rounded-lg border border-slate-300 p-3.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/20 font-sans leading-relaxed"
            />
          </div>

          {validationError && (
            <div role="alert" className="flex items-center gap-2 text-xs font-medium text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{validationError}</span>
            </div>
          )}

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <span className="text-[11px] text-slate-400 font-medium">
              Metadata quarantine active: Only narrative text is ingested for prediction.
            </span>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-sky-700 hover:bg-sky-800 disabled:opacity-50 disabled:cursor-not-allowed px-5 py-2.5 text-xs font-bold text-white shadow-sm transition"
            >
              <Send className="h-3.5 w-3.5" />
              <span>{loading ? 'Analyzing...' : 'Analyze Report'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Loading Indicator */}
      {loading && <LoadingState message="Evaluating precursor mechanisms across dual intelligence engines..." />}

      {/* Error Message */}
      {error && <ErrorState title="Analysis Execution Failed" message={error} onRetry={handleAnalyze} />}

      {/* Analysis Results Display */}
      {result && !loading && (
        <div className="space-y-6">
          {/* Top Level SIF Assessment Banner */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                  Report #{result.report.id} Evaluation
                </span>
                <h2 className="text-xl font-bold tracking-tight text-slate-900">
                  {result.reconciliation.status === 'CONSENSUS_SIF' && (
                    <span className="text-rose-600 flex items-center gap-2">
                      <ShieldAlert className="h-5 w-5" />
                      SIF Precursor Detected
                    </span>
                  )}
                  {result.reconciliation.status === 'CONSENSUS_NON_SIF' && (
                    <span className="text-emerald-600 flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5" />
                      No SIF Precursor Detected
                    </span>
                  )}
                  {result.reconciliation.status === 'DIRECT_DISAGREEMENT' && (
                    <span className="text-purple-700 flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" />
                      Disagreement — Human Review Required
                    </span>
                  )}
                  {result.reconciliation.status.startsWith('RULE_UNCERTAIN') && (
                    <span className="text-amber-600 flex items-center gap-2">
                      <AlertCircle className="h-5 w-5" />
                      Uncertain Evidence — Human Review Required
                    </span>
                  )}
                </h2>
              </div>

              <Link
                to={`/reports/${result.report.id}`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-sky-300 bg-sky-50 px-3.5 py-1.5 text-xs font-semibold text-sky-800 hover:bg-sky-100 hover:border-sky-400 transition"
              >
                <FileText className="h-3.5 w-3.5 text-sky-700" />
                <span>Open Full Audit Record #{result.report.id}</span>
                <ArrowRight className="h-3 w-3" />
              </Link>
            </div>

            {/* Reconciliation Assessment */}
            <div className="pt-4">
              <ReconciliationCard reconciliation={result.reconciliation} />
            </div>
          </div>

          {/* Evidence Channels (ML + Rule) */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <MLEvidenceCard ml={result.ml} />
            <RuleEvidenceCard rule={result.rule} />
          </div>

          {/* Cleaned Narrative Display */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 text-xs">
            <span className="font-bold uppercase tracking-wider text-slate-500 block mb-1">
              Evaluated Incident Narrative
            </span>
            <p className="font-sans text-slate-800 bg-slate-50 p-3 rounded border border-slate-200 leading-relaxed">
              {result.report.narrative}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
