import { apiClient } from './client';
import {
  RecommendationHistoryResponse,
  RecommendationResponse,
  RecommendationRunSummary,
} from '../types';

export interface GenerateRecommendationParams {
  student_id: string;
  top_k?: number;
  weights?: {
    research_interest?: number;
    project_research?: number;
    publication_relevance?: number;
    skill_compatibility?: number;
  };
  filters?: {
    departments?: string[];
    only_accepting_students?: boolean;
    min_capacity?: number;
    data_mode?: 'ALL' | 'REAL_ONLY' | 'SYNTHETIC_ONLY';
    verified_only?: boolean;
  };
}

export const recommendationsApi = {
  generate: async (
    params: GenerateRecommendationParams
  ): Promise<RecommendationResponse> => {
    return apiClient<RecommendationResponse>('/recommendations/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  getRun: async (runId: string): Promise<RecommendationRunSummary> => {
    return apiClient<RecommendationRunSummary>(`/recommendations/runs/${runId}`);
  },

  getHistory: async (studentId: string): Promise<RecommendationHistoryResponse> => {
    return apiClient<RecommendationHistoryResponse>(
      `/recommendations/history/${studentId}`
    );
  },

  submitFeedback: async (
    runId: string,
    facultyId: string,
    rating: number,
    feedbackNotes?: string
  ): Promise<{ status: string; run_id?: string; faculty_id?: string; rating?: number }> => {
    const params = new URLSearchParams();
    params.set('rating', rating.toString());
    if (feedbackNotes && feedbackNotes.trim()) {
      params.set('notes', feedbackNotes.trim());
    }
    return apiClient<{ status: string; run_id?: string; faculty_id?: string; rating?: number }>(
      `/recommendations/runs/${runId}/results/${facultyId}/feedback?${params.toString()}`,
      {
        method: 'POST',
      }
    );
  },
};
