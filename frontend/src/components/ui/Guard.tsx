import type { ReactNode } from "react";
import { useAuthStore } from "../../app/store/auth-store";
import type { UserRole } from "../../features/auth/types";

type GuardProps = {
  children: ReactNode;
  allowedRoles?: UserRole[];
  fallback?: ReactNode;
};

function Guard({ children, allowedRoles, fallback = null }: GuardProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);

  if (!isAuthenticated || !user) {
    return <>{fallback}</>;
  }

  if (allowedRoles && !allowedRoles.includes(user.user_type)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

export default Guard;
