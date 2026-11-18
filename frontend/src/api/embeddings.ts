import { apiClient } from './client';
import { EmbeddingStatsResponse } from '../types';

interface EmbeddingSyncResponse {
  status: string;
  model_name: string;
  model_version: string;
  dimension: number;
  students_embedded?: number;
  projects_embedded?: number;
  faculty_embedded?: number;
  publications_embedded?: number;
}

export const embeddingsApi = {
  sync: async (): Promise<EmbeddingSyncResponse> => {
    return apiClient<EmbeddingSyncResponse>(
      '/embeddings/sync',
      { method: 'POST' }
    );
  },

  syncAll: async (): Promise<EmbeddingSyncResponse> => {
    return apiClient<EmbeddingSyncResponse>(
      '/embeddings/sync',
      { method: 'POST' }
    );
  },

  getStats: async (): Promise<EmbeddingStatsResponse> => {
    return apiClient<EmbeddingStatsResponse>('/embeddings/stats');
  },
};
