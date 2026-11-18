import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { AuthProvider } from './context/AuthContext';
import { AdminDashboard } from './pages/AdminDashboard';
import { FacultyDetailPage } from './pages/FacultyDetailPage';
import { FacultyDirectory } from './pages/FacultyDirectory';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { RecommendationResults } from './pages/RecommendationResults';
import { RegisterPage } from './pages/RegisterPage';
import { StudentDashboard } from './pages/StudentDashboard';
import { StudentProfileEditor } from './pages/StudentProfileEditor';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<AppLayout />}>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/directory" element={<FacultyDirectory />} />
            <Route path="/faculty/:id" element={<FacultyDetailPage />} />

            {/* Student & Recommendations Protected Routes */}
            <Route
              path="/student/dashboard"
              element={
                <ProtectedRoute allowedRoles={['STUDENT', 'ADMIN']}>
                  <StudentDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student/profile/edit"
              element={
                <ProtectedRoute allowedRoles={['STUDENT', 'ADMIN']}>
                  <StudentProfileEditor />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recommendations"
              element={
                <ProtectedRoute allowedRoles={['STUDENT', 'ADMIN']}>
                  <RecommendationResults />
                </ProtectedRoute>
              }
            />

            {/* Admin Protected Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['ADMIN']}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />

            {/* Fallback 404 Route */}
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
