import { apiClient } from './client';
import {
  AcademicProject,
  PaginatedResponse,
  StudentProfile,
  StudentSkillInterest,
} from '../types';

export const studentsApi = {
  getStudent: async (studentId: string): Promise<StudentProfile> => {
    return apiClient<StudentProfile>(`/students/${studentId}`);
  },

  listStudents: async (params?: {
    page?: number;
    page_size?: number;
    department?: string;
    degree_level?: string;
  }): Promise<PaginatedResponse<StudentProfile>> => {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.page_size) query.append('page_size', params.page_size.toString());
    if (params?.department) query.append('department', params.department);
    if (params?.degree_level) query.append('degree_level', params.degree_level);
    const qs = query.toString();
    return apiClient<PaginatedResponse<StudentProfile>>(`/students${qs ? `?${qs}` : ''}`);
  },

  updateStudent: async (
    studentId: string,
    payload: Partial<StudentProfile>
  ): Promise<StudentProfile> => {
    return apiClient<StudentProfile>(`/students/${studentId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  addProject: async (
    studentId: string,
    project: {
      title: string;
      description: string;
      role?: string;
      github_url?: string;
    }
  ): Promise<AcademicProject> => {
    return apiClient<AcademicProject>(`/students/${studentId}/projects`, {
      method: 'POST',
      body: JSON.stringify(project),
    });
  },

  deleteProject: async (
    studentId: string,
    projectId: string
  ): Promise<void> => {
    return apiClient<void>(`/students/${studentId}/projects/${projectId}`, {
      method: 'DELETE',
    });
  },

  addSkill: async (
    studentId: string,
    skill: {
      topic_skill_id: string;
      proficiency_level: number;
      interest_level: number;
      years_experience?: number;
    }
  ): Promise<StudentSkillInterest> => {
    return apiClient<StudentSkillInterest>(`/students/${studentId}/skills`, {
      method: 'POST',
      body: JSON.stringify(skill),
    });
  },

  deleteSkill: async (
    studentId: string,
    skillInterestId: string
  ): Promise<void> => {
    return apiClient<void>(`/students/${studentId}/skills/${skillInterestId}`, {
      method: 'DELETE',
    });
  },
};
