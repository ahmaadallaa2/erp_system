import { Navigate, Outlet } from "react-router";
import { useAuthStore } from "../store/auth-store";
import type { UserRole } from "../../features/auth/types";

type ProtectedRouteProps = {
  allowedRoles?: UserRole[];
};

function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const userRole = useAuthStore((state) => state.user?.role);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && (!userRole || !allowedRoles.includes(userRole))) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}

export default ProtectedRoute;