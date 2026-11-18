import { apiClient } from './client';
import { TopicSkill } from '../types';

export const taxonomyApi = {
  listTopics: async (category?: string, search?: string): Promise<TopicSkill[]> => {
    const query = new URLSearchParams();
    if (category) query.append('category', category);
    if (search) query.append('search', search);
    const qs = query.toString();
    return apiClient<TopicSkill[]>(`/taxonomy/topics${qs ? `?${qs}` : ''}`);
  },
};
