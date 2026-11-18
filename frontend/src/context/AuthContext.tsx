import React, { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../api/auth';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (payload: any) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAdmin: boolean;
  isStudent: boolean;
  isFaculty: boolean;
  studentId: string | null;
  facultyId: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('collab_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = async () => {
    try {
      if (!localStorage.getItem('collab_token')) {
        setUser(null);
        setIsLoading(false);
        return;
      }
      const me = await authApi.getMe();
      setUser(me);
    } catch (error) {
      console.warn('Failed to load user profile session:', error);
      localStorage.removeItem('collab_token');
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCurrentUser();
  }, [token]);

  const login = async (email: string, password: string): Promise<User> => {
    const res = await authApi.login(email, password);
    localStorage.setItem('collab_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const register = async (payload: any) => {
    const res = await authApi.register(payload);
    localStorage.setItem('collab_token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
  };

  const logout = () => {
    localStorage.removeItem('collab_token');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    await fetchCurrentUser();
  };

  const isAdmin = user?.role === 'ADMIN';
  const isStudent = user?.role === 'STUDENT';
  const isFaculty = user?.role === 'FACULTY';
  const studentId = user?.student_id || null;
  const facultyId = user?.faculty_id || null;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
        isAdmin,
        isStudent,
        isFaculty,
        studentId,
        facultyId,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
