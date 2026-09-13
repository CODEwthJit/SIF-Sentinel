import { apiClient } from './api';
import { AnalysisResponse, ReportOut, ReportDetailResponse } from '../types/api';

export const reportService = {
  async analyzeReport(narrative: string): Promise<AnalysisResponse> {
    const response = await apiClient.post<AnalysisResponse>('/reports/analyze', { narrative });
    return response.data;
  },

  async getReports(limit: number = 20, offset: number = 0): Promise<ReportOut[]> {
    const response = await apiClient.get<ReportOut[]>('/reports', {
      params: { limit, offset },
    });
    return response.data;
  },

  async getReportById(reportId: number): Promise<ReportDetailResponse> {
    const response = await apiClient.get<ReportDetailResponse>(`/reports/${reportId}`);
    return response.data;
  },
};

