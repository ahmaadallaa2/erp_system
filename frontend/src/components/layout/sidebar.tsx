import { useEffect, useState } from "react";
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

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const isGeneralRoute = location.pathname.startsWith("/dashboard");
  const isSalesRoute = location.pathname.startsWith("/sales-invoices");
  const isPurchasesRoute = location.pathname.startsWith("/purchase-invoices");
  const isFinanceRoute = location.pathname.startsWith("/payments");
  const isInventoryRoute =
    location.pathname.startsWith("/products") ||
    location.pathname.startsWith("/warehouses") ||
    location.pathname.startsWith("/stock-transactions") ||
    location.pathname.startsWith("/stock-balances") ||
    location.pathname.startsWith("/stock-movements");
  const isAiRoute = location.pathname.startsWith("/ai-assistant");
  const isPartnersRoute = location.pathname.startsWith("/partners");

  if (!isOpen) return null;

  return (
    <aside style={sidebarStyle}>
      <div>
        <div style={brandPanelStyle}>
          <div style={brandMarkStyle}>TB</div>
          <div>
            <h2 style={logoStyle}>ERP System</h2>
            <div style={logoSubtitleStyle}>العمليات</div>
          </div>
        </div>

        <nav style={navStyle}>
          <SidebarSection label="عام" isActive={isGeneralRoute}>
            <SidebarLink to="/dashboard" label="لوحة التحكم" nested />
          </SidebarSection>

          <SidebarSection label="المبيعات" isActive={isSalesRoute}>
            <SidebarLink to="/sales-invoices" label="فواتير المبيعات" nested />
          </SidebarSection>

          <SidebarSection label="المشتريات" isActive={isPurchasesRoute}>
            <SidebarLink to="/purchase-invoices" label="فواتير المشتريات" nested />
          </SidebarSection>

          <SidebarSection label="المالية" isActive={isFinanceRoute}>
            <SidebarLink to="/payments" label="المدفوعات" nested />
          </SidebarSection>

          <SidebarSection label="المخازن" isActive={isInventoryRoute}>
            <SidebarLink to="/products" label="المنتجات" nested />
            <SidebarLink to="/warehouses" label="المخازن" nested />
            <SidebarLink
              to="/stock-transactions"
              label="حركات المخزون"
              nested
            />
            <SidebarLink to="/stock-balances" label="أرصدة المخزون" nested />
            <SidebarLink to="/stock-movements" label="تفاصيل الحركة" nested />
          </SidebarSection>

          <SidebarSection label="الذكاء الاصطناعي" isActive={isAiRoute}>
            <SidebarLink to="/ai-assistant" label="المساعد الذكي" nested />
          </SidebarSection>

          <SidebarSection label="الشركاء" isActive={isPartnersRoute}>
            <SidebarLink to="/partners" label="الشركاء" nested />
          </SidebarSection>
        </nav>
      </div>

      <div style={{ marginTop: "auto", paddingTop: "24px" }}>
        <button onClick={handleLogout} style={logoutButtonStyle}>
          تسجيل الخروج
        </button>
      </div>
    </aside>
  );
}

function SidebarSection({
  label,
  isActive,
  children,
}: {
  label: string;
  isActive: boolean;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    if (isActive) {
      setIsOpen(true);
    }
  }, [isActive]);

  return (
    <div style={sectionStyle}>
      <button
        className="erp-sidebar-button"
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        style={getMenuButtonStyle(isActive)}
      >
        <span>{label}</span>
        <span>{isOpen ? "-" : "+"}</span>
      </button>

      {isOpen && <div style={submenuStyle}>{children}</div>}
    </div>
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
    <Link
      className="erp-sidebar-link"
      to={to}
      style={nested ? getSubLinkStyle(isActive) : getLinkStyle(isActive)}
    >
      {label}
    </Link>
  );
}

const sidebarStyle: React.CSSProperties = {
  width: "272px",
  background: "linear-gradient(180deg, #0f172a 0%, #111827 100%)",
  color: "#fff",
  padding: "20px 16px",
  display: "flex",
  flexDirection: "column",
  flexShrink: 0,
  borderLeft: "1px solid rgba(148, 163, 184, 0.16)",
  boxShadow: "-12px 0 28px rgba(15, 23, 42, 0.08)",
  textAlign: "right",
};

const brandPanelStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
  marginBottom: "22px",
  padding: "10px 10px 14px",
  borderBottom: "1px solid rgba(255,255,255,0.08)",
};

const brandMarkStyle: React.CSSProperties = {
  width: "38px",
  height: "38px",
  borderRadius: "10px",
  background: "rgba(94, 234, 212, 0.16)",
  border: "1px solid rgba(94, 234, 212, 0.32)",
  color: theme.colors.primaryLight,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "13px",
  fontWeight: 900,
};

const logoStyle: React.CSSProperties = {
  margin: 0,
  color: "#f8fafc",
  fontSize: "18px",
  lineHeight: 1.2,
};

const logoSubtitleStyle: React.CSSProperties = {
  marginTop: "2px",
  color: "#94a3b8",
  fontSize: "12px",
  fontWeight: 700,
};

const navStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "8px",
};

const sectionStyle: React.CSSProperties = {
  display: "grid",
  gap: "6px",
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
    borderRadius: "8px",
    border: `1px solid ${isActive ? "rgba(94,234,212,0.38)" : "rgba(255,255,255,0.05)"}`,
    background: isActive ? "rgba(14, 165, 164, 0.95)" : "rgba(255,255,255,0.045)",
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
    color: isActive ? "#ffffff" : "#cbd5e1",
    textDecoration: "none",
    padding: "8px 12px",
    borderRadius: "8px",
    background: isActive ? "rgba(15, 118, 110, 0.82)" : "transparent",
    display: "block",
    fontSize: "13px",
    marginRight: "4px",
    fontWeight: isActive ? 800 : 500,
    border: `1px solid ${isActive ? "rgba(94,234,212,0.20)" : "transparent"}`,
  };
}

const submenuStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "4px",
  paddingRight: "6px",
};

const logoutButtonStyle: React.CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "6px",
  border: "1px solid rgba(255,255,255,0.12)",
  background: "rgba(255,255,255,0.04)",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 700,
};

export default Sidebar;
