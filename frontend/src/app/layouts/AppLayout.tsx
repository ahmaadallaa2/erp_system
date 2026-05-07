import { useState } from "react";
import { Outlet } from "react-router";
import Navbar from "../../components/layout/navbar";
import Sidebar from "../../components/layout/sidebar";
import Footer from "../../components/layout/footer";

function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleToggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f7f7f7",
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