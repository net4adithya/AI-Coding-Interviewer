import { ReactNode } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth, Role } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  allowedRole?: Role;
  children?: ReactNode;
}

export function ProtectedRoute({ allowedRole, children }: ProtectedRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen font-body-main text-secondary">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRole && user.role !== allowedRole) {
    if (user.role === 'authority') {
      return <Navigate to="/authority/dashboard" replace />;
    } else {
      return <Navigate to="/intern/interview/overview" replace />;
    }
  }

  return children ? <>{children}</> : <Outlet />;
}
