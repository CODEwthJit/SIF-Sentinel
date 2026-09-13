import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ReportDetail } from '../pages/ReportDetail';
import { reportService } from '../services/reportService';

vi.mock('../services/reportService');

describe('ReportDetail Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders complete audit breakdown for valid report', async () => {
    vi.mocked(reportService.getReportById).mockResolvedValue({
      report: {
        id: 7,
        narrative: 'An employee was framing a roof and fell 28 feet to the ground when scaffold collapsed.',
        created_at: '2026-09-13T10:00:00Z',
      },
      latest_analysis: {
        report: {
          id: 7,
          narrative: 'An employee was framing a roof and fell 28 feet to the ground when scaffold collapsed.',
          created_at: '2026-09-13T10:00:00Z',
        },
        ml: {
          label: 'YES',
          score: 0.965,
          threshold: 0.59,
          positive_evidence: [{ feature: 'scaffold', contribution: 1.12 }],
          negative_evidence: [],
          decision_rationale: 'Score 0.9650 >= threshold 0.59.',
        },
        rule: {
          label: 'YES',
          reason_code: 'GRAVITATIONAL_EXPOSURE',
          controlling_hazard_energy: 'GRAVITATIONAL',
          barrier_state: 'DAMAGED_OR_MISSING',
          human_exposure: 'DIRECT',
          evidence_sufficiency: 'STRONG',
          precursor_type: 'HIGH_ENERGY_FATAL_COLLAPSE',
          confidence: 'HIGH',
        },
        reconciliation: {
          status: 'CONSENSUS_SIF',
          priority: 'HIGH',
          discrepancy: false,
          review_required: false,
          explanation: 'Full Consensus SIF Precursor.',
        },
      },
      total_analyses: 1,
    });

    render(
      <MemoryRouter initialEntries={['/reports/7']}>
        <Routes>
          <Route path="/reports/:id" element={<ReportDetail />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Incident Audit Report #7')).toBeInTheDocument();
      expect(screen.getByText(/An employee was framing a roof/i)).toBeInTheDocument();
      expect(screen.getByText('Consensus: SIF precursor')).toBeInTheDocument();
      expect(screen.getByText('HIGH PRIORITY')).toBeInTheDocument();
      expect(screen.getByText('0.9650')).toBeInTheDocument();
    });
  });

  it('renders error state when report is not found', async () => {
    vi.mocked(reportService.getReportById).mockRejectedValue(new Error('Report with ID 999 not found.'));

    render(
      <MemoryRouter initialEntries={['/reports/999']}>
        <Routes>
          <Route path="/reports/:id" element={<ReportDetail />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Report Not Found')).toBeInTheDocument();
      expect(screen.getByText(/Report with ID 999 not found/i)).toBeInTheDocument();
    });
  });
});

