import { useEffect, useState } from "react";
import { Outlet } from "react-router";
import Navbar from "../../components/layout/navbar";
import Sidebar from "../../components/layout/sidebar";
import { useAutoLogout } from "../../hooks/useAutoLogout";
import { useAuthStore } from "../store/auth-store";
import { api } from "../../lib/api/axios";
import { API_ENDPOINTS } from "../../lib/api/endpoints";
import type { AuthContext } from "../../features/auth/types";

function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const setAuthContext = useAuthStore((state) => state.setAuthContext);
  const setContextLoading = useAuthStore((state) => state.setContextLoading);
  useAutoLogout();

  useEffect(() => {
    if (!isAuthenticated) return;

    let isMounted = true;

    async function loadAuthContext() {
      setContextLoading(true);

      try {
        const response = await api.get<AuthContext>(API_ENDPOINTS.auth.context);
        if (isMounted) {
          setAuthContext(response.data);
        }
      } catch (err) {
        console.error("Auth context load error:", err);
        if (isMounted) {
          setAuthContext(null);
        }
      } finally {
        if (isMounted) {
          setContextLoading(false);
        }
      }
    }

    loadAuthContext();

    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, setAuthContext, setContextLoading]);

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  return (
    <div
      className="erp-app-shell"
      dir="rtl"
      style={{
        minHeight: "100vh",
        height: "100vh",
        width: "100%",
        maxWidth: "100vw",
        background:
          "radial-gradient(circle at top left, rgba(20, 184, 212, 0.10), transparent 32%), linear-gradient(135deg, #f8fafc 0%, #eef6f8 100%)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          flex: 1,
          minHeight: 0,
          minWidth: 0,
          width: "100%",
          maxWidth: "100vw",
          boxSizing: "border-box",
          overflow: "hidden",
        }}
      >
        <Sidebar isOpen={sidebarOpen} />

        <section
          className="erp-shell-content"
          style={{
            flex: 1,
            minWidth: 0,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            padding: "10px 12px 12px",
            boxSizing: "border-box",
            overflow: "hidden",
          }}
        >
          <Navbar onToggleSidebar={handleToggleSidebar} />

          <main
            className="erp-main-scroll"
            style={{
              flex: 1,
              padding: "14px 0 0",
              boxSizing: "border-box",
              minWidth: 0,
              minHeight: 0,
              width: "100%",
              maxWidth: "100%",
              overflow: "auto",
              background: "transparent",
            }}
          >
            <Outlet />
          </main>
        </section>
      </div>
    </div>
  );
}

export default AppLayout;
