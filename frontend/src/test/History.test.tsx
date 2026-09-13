import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { History } from '../pages/History';
import { reportService } from '../services/reportService';

vi.mock('../services/reportService');

describe('History Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders report list from API', async () => {
    vi.mocked(reportService.getReports).mockResolvedValue([
      {
        id: 1,
        narrative: 'Employee slipped on ice outside.',
        created_at: '2026-09-13T10:00:00Z',
      },
      {
        id: 2,
        narrative: 'Worker fell 30 feet from steel beam.',
        created_at: '2026-09-13T10:05:00Z',
      },
    ]);

    render(
      <BrowserRouter>
        <History />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Incident History')).toBeInTheDocument();
      expect(screen.getByText(/Employee slipped on ice outside/i)).toBeInTheDocument();
      expect(screen.getByText(/Worker fell 30 feet from steel beam/i)).toBeInTheDocument();
    });
  });

  it('filters report list based on search term', async () => {
    vi.mocked(reportService.getReports).mockResolvedValue([
      {
        id: 1,
        narrative: 'Employee slipped on ice outside.',
        created_at: '2026-09-13T10:00:00Z',
      },
      {
        id: 2,
        narrative: 'Worker fell 30 feet from steel beam.',
        created_at: '2026-09-13T10:05:00Z',
      },
    ]);

    render(
      <BrowserRouter>
        <History />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Employee slipped on ice outside/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search.*narrative/i);
    fireEvent.change(searchInput, { target: { value: 'steel beam' } });

    expect(screen.getByText(/Worker fell 30 feet from steel beam/i)).toBeInTheDocument();
    expect(screen.queryByText(/Employee slipped on ice outside/i)).not.toBeInTheDocument();
  });
});

