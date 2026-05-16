import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthContext } from "../../features/auth/types";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  authContext: AuthContext | null;
  isContextLoading: boolean;
  setTokens: (access: string, refresh: string) => void;
  setAuthContext: (context: AuthContext | null) => void;
  setContextLoading: (isLoading: boolean) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      authContext: null,
      isContextLoading: false,

      setTokens: (access, refresh) =>
        set({
          accessToken: access,
          refreshToken: refresh,
          isAuthenticated: true,
          authContext: null,
        }),

      setAuthContext: (context) =>
        set({
          authContext: context,
        }),

      setContextLoading: (isLoading) =>
        set({
          isContextLoading: isLoading,
        }),

      logout: () =>
        set({
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          authContext: null,
          isContextLoading: false,
        }),
    }),
    {
      name: "auth-storage", // اسم في localStorage
    }
  )
);
