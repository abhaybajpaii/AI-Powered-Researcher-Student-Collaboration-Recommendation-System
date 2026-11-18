import { apiClient } from './client';
import { DataCountsResponse, ImportJob, PaginatedResponse } from '../types';

export const adminApi = {
  seedSynthetic: async (params?: {
    num_students?: number;
    num_faculty?: number;
    num_publications?: number;
    seed?: number;
    reset_existing?: boolean;
  }): Promise<{
    status: string;
    job_id: string;
    records_processed: number;
    records_created: number;
    records_updated: number;
  }> => {
    return apiClient<{
      status: string;
      job_id: string;
      records_processed: number;
      records_created: number;
      records_updated: number;
    }>(
      '/admin/seed-synthetic',
      {
        method: 'POST',
        body: JSON.stringify({
          config: params || {},
          reset_existing: params?.reset_existing ?? false,
        }),
      }
    );
  },

  resetSynthetic: async (): Promise<{ status: string; deleted_counts: Record<string, number> }> => {
    return apiClient<{ status: string; deleted_counts: Record<string, number> }>(
      '/admin/reset-synthetic',
      {
        method: 'POST',
      }
    );
  },

  getDataCounts: async (): Promise<DataCountsResponse> => {
    return apiClient<DataCountsResponse>('/admin/data-counts');
  },

  getImportJobs: async (): Promise<PaginatedResponse<ImportJob>> => {
    return apiClient<PaginatedResponse<ImportJob>>('/admin/import-jobs');
  },

  getImportJob: async (jobId: string): Promise<ImportJob> => {
    return apiClient<ImportJob>(`/admin/import-jobs/${jobId}`);
  },

  validateRecords: async (records: {
    topics?: any[];
    students?: any[];
    faculty?: any[];
    publications?: any[];
  }): Promise<{ valid: boolean; summary: Record<string, number>; errors: string[] }> => {
    return apiClient<{ valid: boolean; summary: Record<string, number>; errors: string[] }>('/admin/validate-records', {
      method: 'POST',
      body: JSON.stringify(records),
    });
  },
};
