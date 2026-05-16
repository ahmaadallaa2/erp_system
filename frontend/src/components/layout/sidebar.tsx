import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { useAuthStore } from "../../app/store/auth-store";
import { theme } from "../../styles/theme";

type SidebarProps = {
  isOpen: boolean;
};

function Sidebar({ isOpen }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const [inventoryOpen, setInventoryOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const isInventoryRoute =
    location.pathname.startsWith("/products") ||
    location.pathname.startsWith("/warehouses") ||
    location.pathname.startsWith("/stock-transactions") ||
    location.pathname.startsWith("/stock-balances") ||
    location.pathname.startsWith("/stock-movements");

  if (!isOpen) return null;

  return (
    <aside style={sidebarStyle}>
      <div>
        <h2 style={logoStyle}>ERP System</h2>

        <nav style={navStyle}>
          <SidebarLink to="/dashboard" label="Dashboard" />
          <SidebarLink to="/sales-invoices" label="Sales Invoices" />
          <SidebarLink to="/partners" label="Partners" />
          <SidebarLink to="/purchase-invoices" label="Purchase Invoices" />
          <SidebarLink to="/payments" label="Payments" />
          <SidebarLink to="/ai-assistant" label="AI Assistant" />

          <button
            type="button"
            onClick={() => setInventoryOpen((prev) => !prev)}
            style={getMenuButtonStyle(isInventoryRoute)}
          >
            <span>Inventory</span>
            <span>{inventoryOpen ? "-" : "+"}</span>
          </button>

          {inventoryOpen && (
            <div style={submenuStyle}>
              <SidebarLink to="/products" label="Products" nested />
              <SidebarLink to="/warehouses" label="Warehouses" nested />
              <SidebarLink
                to="/stock-transactions"
                label="Stock Transactions"
                nested
              />
              <SidebarLink to="/stock-balances" label="Stock Balances" nested />
              <SidebarLink to="/stock-movements" label="Stock Movements" nested />
            </div>
          )}
        </nav>
      </div>

      <div style={{ marginTop: "auto", paddingTop: "24px" }}>
        <button onClick={handleLogout} style={logoutButtonStyle}>
          Logout
        </button>
      </div>
    </aside>
  );
}

function SidebarLink({
  to,
  label,
  nested = false,
}: {
  to: string;
  label: string;
  nested?: boolean;
}) {
  const location = useLocation();
  const isActive = location.pathname === to || location.pathname.startsWith(`${to}/`);

  return (
    <Link to={to} style={nested ? getSubLinkStyle(isActive) : getLinkStyle(isActive)}>
      {label}
    </Link>
  );
}

const sidebarStyle: React.CSSProperties = {
  width: "260px",
  background: "#0f172a",
  color: "#fff",
  padding: "22px 16px",
  display: "flex",
  flexDirection: "column",
  flexShrink: 0,
};

const logoStyle: React.CSSProperties = {
  marginTop: 0,
  marginBottom: "22px",
  color: theme.colors.primaryLight,
  fontSize: "20px",
};

const navStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "8px",
};

function getLinkStyle(isActive: boolean): React.CSSProperties {
  return {
    color: "#fff",
    textDecoration: "none",
    padding: "10px 12px",
    borderRadius: "6px",
    background: isActive ? theme.colors.primary : "rgba(255,255,255,0.05)",
    display: "block",
    fontWeight: isActive ? 800 : 600,
    fontSize: "14px",
  };
}

function getMenuButtonStyle(isActive: boolean): React.CSSProperties {
  return {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "6px",
    border: "none",
    background: isActive ? theme.colors.primary : "rgba(255,255,255,0.05)",
    color: "#fff",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    fontSize: "14px",
    fontWeight: isActive ? 800 : 600,
  };
}

function getSubLinkStyle(isActive: boolean): React.CSSProperties {
  return {
    color: "#e5e7eb",
    textDecoration: "none",
    padding: "8px 12px",
    borderRadius: "6px",
    background: isActive ? theme.colors.primaryDark : "transparent",
    display: "block",
    fontSize: "13px",
    marginLeft: "8px",
    fontWeight: isActive ? 800 : 500,
  };
}

const submenuStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "5px",
  paddingLeft: "4px",
};

const logoutButtonStyle: React.CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "6px",
  border: "1px solid rgba(255,255,255,0.12)",
  background: "transparent",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 700,
};

export default Sidebar;
