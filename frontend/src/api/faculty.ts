import { apiClient } from './client';
import { FacultyProfile, PaginatedResponse } from '../types';

export const facultyApi = {
  listFaculty: async (params?: {
    page?: number;
    page_size?: number;
    department?: string;
    accepting_students?: boolean;
    search?: string;
  }): Promise<PaginatedResponse<FacultyProfile>> => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.page_size) query.append('page_size', params.page_size.toString());
    if (params?.department) query.append('department', params.department);
    if (params?.accepting_students !== undefined) {
      query.append('accepting_students', params.accepting_students.toString());
    }
    if (params?.search) query.append('search', params.search);
    const qs = query.toString();
    return apiClient<PaginatedResponse<FacultyProfile>>(`/faculty${qs ? `?${qs}` : ''}`);
  },

  getFaculty: async (facultyId: string): Promise<FacultyProfile> => {
    return apiClient<FacultyProfile>(`/faculty/${facultyId}`);
  },
};
