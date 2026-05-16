import { useState } from "react";
import { Outlet } from "react-router";
import Navbar from "../../components/layout/navbar";
import Sidebar from "../../components/layout/sidebar";
import Footer from "../../components/layout/footer";
import { theme } from "../../styles/theme";
import { useAutoLogout } from "../../hooks/useAutoLogout";

function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  useAutoLogout();

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
