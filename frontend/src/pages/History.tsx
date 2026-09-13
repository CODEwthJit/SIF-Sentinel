import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { History as HistoryIcon, Search, ArrowRight, ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { reportService } from '../services/reportService';
import { ReportOut } from '../types/api';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

const PAGE_SIZE = 10;

export const History: React.FC = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<ReportOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [offset, setOffset] = useState(0);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await reportService.getReports(PAGE_SIZE, offset);
      setReports(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch report history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [offset]);

  const filteredReports = reports.filter((r) =>
    r.narrative.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Incident History</h1>
          <p className="text-xs text-slate-500 mt-1">
            Previously analyzed safety reports and classification audit trails.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search incident narratives..."
            aria-label="Search incident narratives"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-slate-300 py-2 pl-9 pr-3 text-xs text-slate-800 placeholder:text-slate-400 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/20 shadow-sm"
          />
        </div>
      </div>

      {loading && <LoadingState message="Fetching incident history..." />}
      {error && <ErrorState title="History Load Error" message={error} onRetry={fetchReports} />}

      {!loading && !error && reports.length === 0 && (
        <EmptyState
          title="No reports analyzed yet."
          description="There are currently no safety narratives recorded in your account. Analyze your first report to start generating precursor intelligence."
          actionLabel="Analyze your first report"
          onAction={() => navigate('/analyze')}
        />
      )}

      {!loading && !error && reports.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4 w-20">ID</th>
                  <th className="py-3 px-4">Narrative Text</th>
                  <th className="py-3 px-4 w-44">Date Analyzed</th>
                  <th className="py-3 px-4 w-28 text-right">Audit Detail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {filteredReports.map((report) => (
                  <tr key={report.id} className="hover:bg-slate-50/80 transition group">
                    <td className="py-3.5 px-4 font-mono font-semibold text-slate-500">#{report.id}</td>
                    <td className="py-3.5 px-4 text-slate-800 font-medium leading-relaxed max-w-xl">
                      {report.narrative}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px] whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-3 w-3 text-slate-400" />
                        <span>{new Date(report.created_at).toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <Link
                        to={`/reports/${report.id}`}
                        className="inline-flex items-center gap-1 font-semibold text-sky-700 hover:text-sky-900 bg-sky-50 px-2.5 py-1 rounded border border-sky-200 group-hover:border-sky-300 transition"
                      >
                        <span>Audit</span>
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50 px-4 py-3 text-xs text-slate-500">
            <span>
              Showing reports {offset + 1} to {offset + filteredReports.length}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0}
                className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-2.5 py-1 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Previous
              </button>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={reports.length < PAGE_SIZE}
                className="inline-flex items-center gap-1 rounded border border-slate-300 bg-white px-2.5 py-1 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition"
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

