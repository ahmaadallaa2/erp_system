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
          <Link
            to="/dashboard"
            style={getLinkStyle(location.pathname === "/dashboard")}
          >
            Dashboard
          </Link>

          <Link
            to="/sales-invoices"
            style={getLinkStyle(location.pathname === "/sales-invoices")}
          >
            Sales Invoices
          </Link>

          <Link
            to="/partners"
            style={getLinkStyle(location.pathname === "/partners")}
          >
            Partners
          </Link>

          <Link
            to="/purchase-invoices"
            style={getLinkStyle(location.pathname === "/purchase-invoices")}
          >
            Purchase Invoices
          </Link>

          <button
            type="button"
            onClick={() => setInventoryOpen((prev) => !prev)}
            style={getMenuButtonStyle(isInventoryRoute)}
          >
            <span>Inventory</span>
            <span>{inventoryOpen ? "−" : "+"}</span>
          </button>

          {inventoryOpen && (
            <div style={submenuStyle}>
              <Link
                to="/products"
                style={getSubLinkStyle(location.pathname === "/products")}
              >
                Products
              </Link>

              <Link
                to="/warehouses"
                style={getSubLinkStyle(location.pathname === "/warehouses")}
              >
                Warehouses
              </Link>

              <Link
                to="/stock-transactions"
                style={getSubLinkStyle(
                  location.pathname === "/stock-transactions"
                )}
              >
                Stock Transactions
              </Link>

              <Link
                to="/stock-balances"
                style={getSubLinkStyle(location.pathname === "/stock-balances")}
              >
                Stock Balances
              </Link>

              <Link
                to="/stock-movements"
                style={getSubLinkStyle(location.pathname === "/stock-movements")}
              >
                Stock Movements
              </Link>
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

const sidebarStyle: React.CSSProperties = {
  width: "260px",
  background: "#0f172a", // dark modern
  color: "#fff",
  padding: "24px 16px",
  display: "flex",
  flexDirection: "column",
};

const logoStyle: React.CSSProperties = {
  marginTop: 0,
  marginBottom: "24px",
  color: theme.colors.primary,
};

const navStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "10px",
};

function getLinkStyle(isActive: boolean): React.CSSProperties {
  return {
    color: "#fff",
    textDecoration: "none",
    padding: "10px 12px",
    borderRadius: "8px",
    background: isActive
      ? theme.colors.primary
      : "rgba(255,255,255,0.05)",
    display: "block",
    fontWeight: isActive ? 700 : 500,
    transition: "all 0.2s ease",
  };
}

function getMenuButtonStyle(isActive: boolean): React.CSSProperties {
  return {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "8px",
    border: "none",
    background: isActive
      ? theme.colors.primary
      : "rgba(255,255,255,0.05)",
    color: "#fff",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    fontSize: "14px",
    fontWeight: isActive ? 700 : 500,
  };
}

function getSubLinkStyle(isActive: boolean): React.CSSProperties {
  return {
    color: "#e5e7eb",
    textDecoration: "none",
    padding: "8px 12px",
    borderRadius: "8px",
    background: isActive
      ? theme.colors.primaryDark
      : "transparent",
    display: "block",
    fontSize: "13px",
    marginLeft: "8px",
  };
}

const submenuStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "6px",
  paddingLeft: "4px",
};

const logoutButtonStyle: React.CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "8px",
  border: "1px solid rgba(255,255,255,0.1)",
  background: "transparent",
  color: "#fff",
  cursor: "pointer",
};

export default Sidebar;