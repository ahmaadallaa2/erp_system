import { create } from "zustand";
import { persist } from "zustand/middleware";
<<<<<<< HEAD
import type { AuthContext, AuthUser } from "../../features/auth/types";
=======
import type { AuthContext } from "../../features/auth/types";
>>>>>>> d3e37ff92beaff7ff7813a7d60c19b113c1ce48b

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  authContext: AuthContext | null;
<<<<<<< HEAD
  user: AuthUser | null;
=======
>>>>>>> d3e37ff92beaff7ff7813a7d60c19b113c1ce48b
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
<<<<<<< HEAD
      user: null,
=======
>>>>>>> d3e37ff92beaff7ff7813a7d60c19b113c1ce48b
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

      setAuthContext: (context) =>
        set({
          authContext: context,
          user: context?.user ?? null,
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
<<<<<<< HEAD
          user: null,
=======
>>>>>>> d3e37ff92beaff7ff7813a7d60c19b113c1ce48b
          isContextLoading: false,
        }),
    }),
    {
      name: "auth-storage", // اسم في localStorage
    }
  )
);
