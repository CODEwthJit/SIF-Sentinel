import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Calendar, FileText, ShieldAlert, CheckCircle2, AlertTriangle, AlertCircle, Shield } from 'lucide-react';
import { reportService } from '../services/reportService';
import { ReportDetailResponse } from '../types/api';
import { MLEvidenceCard } from '../components/MLEvidenceCard';
import { RuleEvidenceCard } from '../components/RuleEvidenceCard';
import { ReconciliationCard } from '../components/ReconciliationCard';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

export const ReportDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [detail, setDetail] = useState<ReportDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await reportService.getReportById(parseInt(id, 10));
      setDetail(data);
    } catch (err: any) {
      setError(err.message || `Failed to load report #${id}.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  if (loading) {
    return <LoadingState message={`Fetching analysis audit trail for report #${id}...`} />;
  }

  if (error || !detail) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link
            to="/history"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Incident History</span>
          </Link>
          <span className="text-slate-300">|</span>
          <Link
            to="/dashboard"
            className="text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
          >
            Go to Dashboard
          </Link>
        </div>
        <ErrorState
          title="Report Not Found"
          message={error || `Report #${id} could not be retrieved from the database.`}
          onRetry={fetchDetail}
        />
      </div>
    );
  }

  const { report, latest_analysis } = detail;

  return (
    <div className="space-y-8">
      {/* Back Link & Header */}
      <div>
        <Link
          to="/history"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 mb-3 transition"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Incident History</span>
        </Link>
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
              <span>Incident Audit Report #{report.id}</span>
            </h1>
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-500 font-mono">
              <Calendar className="h-3.5 w-3.5 text-slate-400" />
              <span>Analyzed: {new Date(report.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Raw Incident Narrative Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3 mb-3">
          <FileText className="h-4 w-4 text-sky-700" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
            Safety Incident Narrative
          </h2>
        </div>
        <p className="font-sans text-sm text-slate-800 leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-200">
          {report.narrative}
        </p>
      </div>

      {/* Latest Analysis Breakdown */}
      {latest_analysis ? (
        <div className="space-y-6">
          {/* Assessment Overview Banner */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Primary Assessment
            </span>
            <div className="text-xl font-bold tracking-tight text-slate-900 mb-4">
              {latest_analysis.reconciliation.status === 'CONSENSUS_SIF' && (
                <span className="text-rose-600 flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5" />
                  Consensus: SIF Precursor Detected
                </span>
              )}
              {latest_analysis.reconciliation.status === 'CONSENSUS_NON_SIF' && (
                <span className="text-emerald-600 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5" />
                  Consensus: Non-SIF Incident
                </span>
              )}
              {latest_analysis.reconciliation.status === 'DIRECT_DISAGREEMENT' && (
                <span className="text-purple-700 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  Direct Disagreement — Human Review Required
                </span>
              )}
              {latest_analysis.reconciliation.status.startsWith('RULE_UNCERTAIN') && (
                <span className="text-amber-600 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Uncertain Evidence — Human Review Required
                </span>
              )}
            </div>

            <ReconciliationCard reconciliation={latest_analysis.reconciliation} />
          </div>

          {/* Evidence Cards */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <MLEvidenceCard ml={latest_analysis.ml} />
            <RuleEvidenceCard rule={latest_analysis.rule} />
          </div>

          {/* Technical Governance & Audit Disclaimer */}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-6 text-xs text-slate-600 space-y-3">
            <div className="flex items-center gap-2 font-bold text-slate-800 uppercase tracking-wider text-[11px]">
              <Shield className="h-4 w-4 text-sky-700" />
              <span>Scientific &amp; Technical Governance Audit Trail</span>
            </div>
            <p className="leading-relaxed">
              This triage record was generated by the SIF Sentinel dual-engine evaluation framework. 
              The statistical branch employs TF-IDF vectorization and locked logistic regression (decision threshold &tau; = 0.59) 
              calibrated against historical safety datasets. The deterministic branch applies physics-based gravitational and mechanical hazard energy precedence rules.
            </p>
            <div className="p-3 bg-white rounded border border-slate-200 text-[11px] text-slate-500 italic">
              AI-assisted safety decision support for qualified EHS professionals. Not an autonomous safety decision maker. 
              Uncertain or conflicting assessments require qualified human safety review.
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-xs text-slate-500">
          No analysis pipeline execution recorded for this report.
        </div>
      )}
    </div>
  );
};
