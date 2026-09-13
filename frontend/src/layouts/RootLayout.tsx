import React, { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { dashboardService } from '../services/dashboardService';
import { HealthStatus } from '../types/api';
import { Activity, ShieldAlert, Menu, X } from 'lucide-react';

export const RootLayout: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    dashboardService
      .getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <div className="flex h-screen w-full bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar Navigation (Desktop + Mobile Drawer) */}
      <Sidebar mobileOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Operational Header */}
        <header className="h-16 flex-shrink-0 bg-white border-b border-slate-200 px-4 md:px-8 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
              className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 md:hidden"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            <div>
              <span className="text-[10px] md:text-xs font-semibold uppercase tracking-wider text-sky-600 block">
                AI-Powered Safety Intelligence
              </span>
              <h2 className="text-xs md:text-sm font-bold text-slate-900 truncate">
                SIF Sentinel Platform
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {health ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 border border-emerald-200 whitespace-nowrap">
                <Activity className="h-3 w-3 animate-pulse text-emerald-600" />
                <span className="hidden sm:inline">Engine Operational</span> (v{health.version})
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700 border border-amber-200 whitespace-nowrap">
                <ShieldAlert className="h-3 w-3 text-amber-600" />
                <span>Backend Offline</span>
              </span>
            )}
          </div>
        </header>

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-7xl mx-auto space-y-8 pb-12">
            <Outlet />
          </div>
        </main>

        {/* Concise Safety Governance Footer */}
        <footer className="flex-shrink-0 bg-slate-100 border-t border-slate-200 px-4 md:px-8 py-2.5 text-[11px] text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-1 text-center sm:text-left">
          <span className="font-medium text-slate-700">
            SIF Sentinel — AI-assisted decision support for qualified EHS professionals.
          </span>
          <span className="text-slate-500">
            AI-assisted safety triage. Uncertain or conflicting assessments require human review.
          </span>
        </footer>
      </div>
    </div>
  );
};

