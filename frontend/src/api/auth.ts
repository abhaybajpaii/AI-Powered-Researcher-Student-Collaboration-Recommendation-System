import { apiClient } from './client';
import { AuthResponse, User } from '../types';

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    return apiClient<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

  register: async (payload: {
    email: string;
    password: string;
    role: 'STUDENT' | 'FACULTY' | 'ADMIN';
    first_name: string;
    last_name: string;
    department: string;
    bio?: string;
    statement_of_purpose?: string;
  }): Promise<AuthResponse> => {
    return apiClient<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getMe: async (): Promise<User> => {
    return apiClient<User>('/auth/me');
  },
};
