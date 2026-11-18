import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: ('STUDENT' | 'FACULTY' | 'ADMIN')[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
}) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="py-20">
        <LoadingSpinner message="Checking authentication session..." size="lg" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="text-center py-20 px-4">
        <h2 className="text-xl font-bold text-rose-400 mb-2">Access Restricted</h2>
        <p className="text-sm text-slate-400 max-w-md mx-auto mb-6">
          Your current account role ({user.role}) does not have permission to access this portal. Required: {allowedRoles.join(', ')}.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};
