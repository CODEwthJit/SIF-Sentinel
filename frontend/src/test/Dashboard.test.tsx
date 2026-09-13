import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Dashboard } from '../pages/Dashboard';
import { dashboardService } from '../services/dashboardService';

vi.mock('../services/dashboardService');

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(dashboardService.getDashboardStats).mockReturnValue(new Promise(() => {}));
    vi.mocked(dashboardService.getDashboardRecent).mockReturnValue(new Promise(() => {}));

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    expect(screen.getByText(/Loading EHS safety analytics dashboard/i)).toBeInTheDocument();
  });

  it('renders KPI metrics and recent analysis feed on API success', async () => {
    vi.mocked(dashboardService.getDashboardStats).mockResolvedValue({
      total_reports: 147,
      total_analyses: 147,
      consensus_sif_count: 116,
      consensus_non_sif_count: 26,
      discrepancy_count: 5,
      high_priority_count: 121,
      medium_priority_count: 0,
      low_priority_count: 26,
      reconciliation_status_distribution: {
        CONSENSUS_SIF: 116,
        CONSENSUS_NON_SIF: 26,
        DIRECT_DISAGREEMENT: 5,
      },
      review_priority_distribution: {
        HIGH: 121,
        LOW: 26,
      },
      rule_reason_code_distribution: {
        GRAVITATIONAL_EXPOSURE: 65,
      },
      hazard_energy_distribution: {
        GRAVITATIONAL: 65,
      },
    });

    vi.mocked(dashboardService.getDashboardRecent).mockResolvedValue({
      total_returned: 1,
      recent_analyses: [
        {
          report_id: 101,
          narrative_preview: 'Worker fell from scaffold elevation.',
          ml_label: 'YES',
          ml_score: 0.985,
          rule_label: 'YES',
          reconciliation_status: 'CONSENSUS_SIF',
          review_priority: 'HIGH',
          human_review_required: false,
          created_at: '2026-09-13T10:00:00Z',
        },
      ],
    });

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('SIF Sentinel')).toBeInTheDocument();
      expect(screen.getByText(/Safety Intelligence Overview/i)).toBeInTheDocument();
      expect(screen.getByText('147')).toBeInTheDocument();
      expect(screen.getByText('116')).toBeInTheDocument();
      expect(screen.getByText('Recent Incident Triage Feed')).toBeInTheDocument();
      expect(screen.getByText(/Worker fell from scaffold/i)).toBeInTheDocument();
    });
  });

  it('renders error state when API fails', async () => {
    vi.mocked(dashboardService.getDashboardStats).mockRejectedValue(new Error('Backend connection failed'));
    vi.mocked(dashboardService.getDashboardRecent).mockResolvedValue({ total_returned: 0, recent_analyses: [] });

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Dashboard Connection Error')).toBeInTheDocument();
      expect(screen.getByText(/Backend connection failed/i)).toBeInTheDocument();
    });
  });
});

