import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  ArrowRight,
  TrendingUp,
  Layers,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from 'recharts';

import { dashboardService } from '../services/dashboardService';
import { DashboardStats, DashboardRecent } from '../types/api';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/StatusBadge';
import { PriorityBadge } from '../components/PriorityBadge';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recent, setRecent] = useState<DashboardRecent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, recentData] = await Promise.all([
        dashboardService.getDashboardStats(),
        dashboardService.getDashboardRecent(6),
      ]);
      setStats(statsData);
      setRecent(recentData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard statistics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return <LoadingState message="Loading EHS safety analytics dashboard..." />;
  }

  if (error) {
    return <ErrorState title="Dashboard Connection Error" message={error} onRetry={fetchDashboardData} />;
  }

  if (!stats || (stats.total_reports === 0 && stats.total_analyses === 0)) {
    return (
      <EmptyState
        title="No Incident Reports Analyzed Yet"
        description="The database currently contains no analyzed safety narratives. Analyze your first incident report to populate the analytics dashboard."
        actionLabel="Analyze Incident Report"
        onAction={() => navigate('/analyze')}
      />
    );
  }

  // Format Recharts data
  const statusChartData = Object.entries(stats.reconciliation_status_distribution || {}).map(([key, val]) => ({
    name: key.replace(/_/g, ' '),
    count: val,
  }));

  const priorityChartData = Object.entries(stats.review_priority_distribution || {}).map(([key, val]) => ({
    name: `${key} Priority`,
    value: val,
  }));

  const reasonChartData = Object.entries(stats.rule_reason_code_distribution || {})
    .slice(0, 6)
    .map(([key, val]) => ({
      name: key.replace(/_/g, ' '),
      count: val,
    }));

  const energyChartData = Object.entries(stats.hazard_energy_distribution || {})
    .slice(0, 6)
    .map(([key, val]) => ({
      name: key.replace(/_/g, ' '),
      count: val,
    }));

  const PRIORITY_COLORS: Record<string, string> = {
    'HIGH Priority': '#dc2626',
    'MEDIUM Priority': '#d97706',
    'LOW Priority': '#059669',
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 font-mono">SIF Sentinel</h1>
            <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600 border border-slate-200">
              Overview
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Safety Intelligence Overview — Real-time precursor signals, triage metrics, and risk distributions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* System Status Indicator */}
          <div className="hidden sm:flex items-center gap-2 bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs shadow-sm">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-medium text-slate-700">AI Engine:</span>
            <span className="text-emerald-700 font-semibold">Operational</span>
            <span className="text-slate-300">|</span>
            <span className="font-medium text-slate-700">API:</span>
            <span className="text-emerald-700 font-semibold">Connected</span>
          </div>

          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 rounded-lg bg-sky-700 hover:bg-sky-800 px-4 py-2 text-xs font-semibold text-white shadow-sm transition"
          >
            <span>Analyze Report</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid (4 Core Business Metrics) */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Reports Analyzed"
          value={stats.total_reports}
          subtitle="Total persistent records"
          icon={FileSpreadsheet}
          variant="default"
        />
        <StatCard
          title="SIF Signals"
          value={stats.consensus_sif_count}
          subtitle="Precursor events identified"
          icon={ShieldAlert}
          variant="danger"
        />
        <StatCard
          title="Non-SIF"
          value={stats.consensus_non_sif_count}
          subtitle="Routine / low-energy incidents"
          icon={CheckCircle2}
          variant="success"
        />
        <StatCard
          title="Human Reviews"
          value={stats.discrepancy_count}
          subtitle="Discrepancies & edge cases"
          icon={AlertTriangle}
          variant="warning"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Status Distribution */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-4 flex items-center gap-2">
            <Layers className="h-4 w-4 text-sky-600" />
            Categorical Reconciliation Status
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={statusChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '11px',
                  }}
                />
                <Bar dataKey="count" fill="#0284c7" radius={[4, 4, 0, 0]}>
                  {statusChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.name.includes('SIF') && !entry.name.includes('NON')
                          ? '#dc2626'
                          : entry.name.includes('DISAGREEMENT')
                          ? '#7c3aed'
                          : entry.name.includes('UNCERTAIN')
                          ? '#d97706'
                          : '#059669'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Review Priority Distribution */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-amber-600" />
            Operational Review Priority Distribution
          </h3>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={priorityChartData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={50}
                  paddingAngle={4}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {priorityChartData.map((entry, index) => (
                    <Cell key={`slice-${index}`} fill={PRIORITY_COLORS[entry.name] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '11px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hazard Energy Distribution */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-4">
            Top Controlling Hazard Energies
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={energyChartData}
                layout="vertical"
                margin={{ top: 5, right: 20, left: 40, bottom: 5 }}
              >
                <XAxis type="number" tick={{ fontSize: 10 }} allowDecimals={false} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={90} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '11px',
                  }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Rule Reason Code Distribution */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-4">
            Top V2.3 Rule Reason Codes
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={reasonChartData}
                layout="vertical"
                margin={{ top: 5, right: 20, left: 40, bottom: 5 }}
              >
                <XAxis type="number" tick={{ fontSize: 10 }} allowDecimals={false} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={120} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '11px',
                  }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Incident Triage Table */}
      {recent && recent.recent_analyses && recent.recent_analyses.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-900">
                Recent Incident Triage Feed
              </h3>
              <p className="text-xs text-slate-500">Live stream of pipeline assessments</p>
            </div>
            <Link
              to="/history"
              className="text-xs font-semibold text-sky-700 hover:text-sky-800 flex items-center gap-1"
            >
              <span>View Full History</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-3">Report ID</th>
                  <th className="py-3 px-3">Incident Narrative Preview</th>
                  <th className="py-3 px-3">ML Score</th>
                  <th className="py-3 px-3">Reconciliation Status</th>
                  <th className="py-3 px-3">Priority</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recent.recent_analyses.map((item) => (
                  <tr key={item.report_id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3 px-3 font-mono font-medium text-slate-500">#{item.report_id}</td>
                    <td className="py-3 px-3 max-w-xs truncate text-slate-800 font-medium">
                      {item.narrative_preview}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-700">{item.ml_score.toFixed(4)}</td>
                    <td className="py-3 px-3">
                      <StatusBadge status={item.reconciliation_status} size="sm" />
                    </td>
                    <td className="py-3 px-3">
                      <PriorityBadge priority={item.review_priority} size="sm" />
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        to={`/reports/${item.report_id}`}
                        className="inline-flex items-center gap-1 font-semibold text-sky-700 hover:text-sky-900"
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
        </div>
      )}
    </div>
  );
};

