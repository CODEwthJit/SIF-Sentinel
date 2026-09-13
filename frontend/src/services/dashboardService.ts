import { apiClient } from './api';
import { DashboardStats, DashboardRecent, HealthStatus } from '../types/api';

export const dashboardService = {
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },

  async getDashboardRecent(limit: number = 10): Promise<DashboardRecent> {
    const response = await apiClient.get<DashboardRecent>('/dashboard/recent', {
      params: { limit },
    });
    return response.data;
  },

  async getHealth(): Promise<HealthStatus> {
    const response = await apiClient.get<HealthStatus>('/health');
    return response.data;
  },
};

