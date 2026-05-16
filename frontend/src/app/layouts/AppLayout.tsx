import { useEffect, useState } from "react";
import { Outlet } from "react-router";
import Navbar from "../../components/layout/navbar";
import Sidebar from "../../components/layout/sidebar";
import Footer from "../../components/layout/footer";
import { theme } from "../../styles/theme";
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
      style={{
        minHeight: "100vh",
        background: theme.colors.background,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Navbar onToggleSidebar={handleToggleSidebar} />

      <div style={{ display: "flex", flex: 1 }}>
        <Sidebar isOpen={sidebarOpen} />

        <main
          style={{
            flex: 1,
            padding: "24px",
            minWidth: 0,
          }}
        >
          <Outlet />
        </main>
      </div>

      <Footer />
    </div>
  );
}

export default AppLayout;
