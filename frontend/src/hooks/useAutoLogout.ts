import { useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import toast from "react-hot-toast";
import { useAuthStore } from "../app/store/auth-store";

export const AUTO_LOGOUT_MINUTES = 30;

const AUTO_LOGOUT_DELAY_MS = AUTO_LOGOUT_MINUTES * 60 * 1000;
const ACTIVITY_EVENTS = [
  "mousemove",
  "keydown",
  "click",
  "scroll",
  "touchstart",
] as const;

export function useAutoLogout() {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const logout = useAuthStore((state) => state.logout);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      clearLogoutTimer(timeoutRef);
      return;
    }

    const handleTimeout = () => {
      logout();
      toast("You were logged out after 30 minutes of inactivity.");
      navigate("/login", { replace: true });
    };

    const resetTimer = () => {
      clearLogoutTimer(timeoutRef);
      timeoutRef.current = window.setTimeout(handleTimeout, AUTO_LOGOUT_DELAY_MS);
    };

    resetTimer();

    ACTIVITY_EVENTS.forEach((eventName) => {
      window.addEventListener(eventName, resetTimer, { passive: true });
    });

    return () => {
      clearLogoutTimer(timeoutRef);
      ACTIVITY_EVENTS.forEach((eventName) => {
        window.removeEventListener(eventName, resetTimer);
      });
    };
  }, [isAuthenticated, logout, navigate]);
}

function clearLogoutTimer(timeoutRef: React.MutableRefObject<number | null>) {
  if (timeoutRef.current !== null) {
    window.clearTimeout(timeoutRef.current);
    timeoutRef.current = null;
  }
}
