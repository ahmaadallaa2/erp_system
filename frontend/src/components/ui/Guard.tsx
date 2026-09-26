import type { ReactNode } from "react";
import { useAuthStore } from "../../app/store/auth-store";
import type { Permission, UserRole } from "../../features/auth/types";

type GuardProps = {
  children: ReactNode;
  allowedRoles?: UserRole[];
  permissions?: Permission[];
  fallback?: ReactNode;
};

function Guard({ children, allowedRoles, permissions, fallback = null }: GuardProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const userRole = user?.role;
  const userPermissions = user?.permissions ?? [];

  if (!isAuthenticated || !user) {
    return <>{fallback}</>;
  }

  const roleAllowed = !allowedRoles || allowedRoles.includes(userRole);
  const permissionsAllowed =
    !permissions || permissions.every((permission) => userPermissions.includes(permission));

  if (!roleAllowed || !permissionsAllowed) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

export default Guard;
