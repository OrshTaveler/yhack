import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import type { UserRole } from '@/types';

interface RoleGuardProps {
  allowed: UserRole[];
}

export function RoleGuard({ allowed }: RoleGuardProps) {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowed.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
