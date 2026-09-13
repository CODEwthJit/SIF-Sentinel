import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Analyze } from '../pages/Analyze';
import { reportService } from '../services/reportService';

vi.mock('../services/reportService');

describe('Analyze Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders input area, benchmark buttons, and analyze action', () => {
    render(
      <BrowserRouter>
        <Analyze />
      </BrowserRouter>
    );

    expect(screen.getByText('Analyze Safety Report')).toBeInTheDocument();
    expect(screen.getByLabelText(/Report Narrative/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze Report/i })).toBeInTheDocument();
  });

  it('validates empty narrative input gracefully', async () => {
    render(
      <BrowserRouter>
        <Analyze />
      </BrowserRouter>
    );

    const button = screen.getByRole('button', { name: /Analyze Report/i });
    fireEvent.click(button);

    expect(screen.getByText(/Narrative cannot be empty or whitespace-only/i)).toBeInTheDocument();
    expect(reportService.analyzeReport).not.toHaveBeenCalled();
  });

  it('validates whitespace-only narrative input gracefully', async () => {
    render(
      <BrowserRouter>
        <Analyze />
      </BrowserRouter>
    );

    const textarea = screen.getByLabelText(/Report Narrative/i);
    fireEvent.change(textarea, { target: { value: '   \n\t   ' } });

    const button = screen.getByRole('button', { name: /Analyze Report/i });
    fireEvent.click(button);

    expect(screen.getByText(/Narrative cannot be empty or whitespace-only/i)).toBeInTheDocument();
    expect(reportService.analyzeReport).not.toHaveBeenCalled();
  });

  it('renders complete SIF assessment and evidence cards on API success', async () => {
    vi.mocked(reportService.analyzeReport).mockResolvedValue({
      report: {
        id: 42,
        narrative: 'An employee fell 28 feet from a scaffold after the scaffold collapsed.',
        created_at: '2026-09-13T10:00:00Z',
      },
      ml: {
        label: 'YES',
        score: 0.9966,
        threshold: 0.59,
        positive_evidence: [{ feature: 'fell', contribution: 1.48 }],
        negative_evidence: [],
        decision_rationale: 'Score 0.9966 >= threshold 0.59.',
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
        explanation: 'Full Consensus SIF Precursor: ML predicts YES and V2.3 predicts YES.',
      },
    });

    render(
      <BrowserRouter>
        <Analyze />
      </BrowserRouter>
    );

    const textarea = screen.getByLabelText(/Report Narrative/i);
    fireEvent.change(textarea, {
      target: { value: 'An employee fell 28 feet from a scaffold after the scaffold collapsed.' },
    });

    const button = screen.getByRole('button', { name: /Analyze Report/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Report #42 Evaluation/i)).toBeInTheDocument();
      expect(screen.getByText('Consensus: SIF precursor')).toBeInTheDocument();
      expect(screen.getByText('HIGH PRIORITY')).toBeInTheDocument();
      expect(screen.getByText('GRAVITATIONAL')).toBeInTheDocument();
      expect(screen.getByText('0.9966')).toBeInTheDocument();
      expect(screen.getByText(/Open Full Audit Record #42/i)).toBeInTheDocument();
    });
  });

  it('renders prominent warning for direct disagreement', async () => {
    vi.mocked(reportService.analyzeReport).mockResolvedValue({
      report: {
        id: 99,
        narrative: 'Employee was trapped under conveyor belt bar.',
        created_at: '2026-09-13T10:00:00Z',
      },
      ml: {
        label: 'YES',
        score: 0.92,
        threshold: 0.59,
        positive_evidence: [{ feature: 'trapped', contribution: 1.2 }],
        negative_evidence: [],
      },
      rule: {
        label: 'NO',
        reason_code: 'LOW_ENERGY_EQUIPMENT',
        controlling_hazard_energy: 'MECHANICAL',
        barrier_state: 'FUNCTIONAL',
        human_exposure: 'INDIRECT',
        evidence_sufficiency: 'STRONG',
      },
      reconciliation: {
        status: 'DIRECT_DISAGREEMENT',
        priority: 'HIGH',
        discrepancy: true,
        review_required: true,
        explanation: 'Model and rule engine disagree: ML predicts YES but rule predicts NO.',
      },
    });

    render(
      <BrowserRouter>
        <Analyze />
      </BrowserRouter>
    );

    const textarea = screen.getByLabelText(/Report Narrative/i);
    fireEvent.change(textarea, {
      target: { value: 'Employee was trapped under conveyor belt bar.' },
    });

    const button = screen.getByRole('button', { name: /Analyze Report/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(
        screen.getByText('Model and rule engine disagree — human review required.')
      ).toBeInTheDocument();
      expect(screen.getByText('Disagreement — Review required')).toBeInTheDocument();
    });
  });

  it('renders error state on API failure', async () => {
    vi.mocked(reportService.analyzeReport).mockRejectedValue(new Error('Pipeline service error'));

    render(
      <BrowserRouter>
        <Analyze />
      </BrowserRouter>
    );

    const textarea = screen.getByLabelText(/Report Narrative/i);
    fireEvent.change(textarea, { target: { value: 'Test incident narrative' } });

    const button = screen.getByRole('button', { name: /Analyze Report/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Analysis Execution Failed')).toBeInTheDocument();
      expect(screen.getByText(/Pipeline service error/i)).toBeInTheDocument();
    });
  });
});
