import { theme } from "../../styles/theme";
import { useAuthStore } from "../../app/store/auth-store";

type NavbarProps = {
  onToggleSidebar: () => void;
};

function Navbar({ onToggleSidebar }: NavbarProps) {
  const authContext = useAuthStore((state) => state.authContext);
  const isContextLoading = useAuthStore((state) => state.isContextLoading);
  const companyName = isContextLoading ? "..." : authContext?.company?.name || "-";
  const branchName = isContextLoading ? "..." : authContext?.branch?.name || "-";

  return (
    <header style={navbarStyle}>
      <div style={leftSectionStyle}>
        <button className="erp-navbar-button" onClick={onToggleSidebar} style={toggleButtonStyle}>
          القائمة
        </button>

        <div>
          <strong style={titleStyle}>TB ERP System</strong>
          <div style={subtitleStyle}>مساحة عمل العمليات الداخلية</div>
        </div>
      </div>

      <div style={rightSectionStyle}>
        <div style={contextBlockStyle}>
          <span style={contextItemStyle}>الشركة: {companyName}</span>
          <span style={contextItemStyle}>الفرع: {branchName}</span>
        </div>
        <span style={brandStyle}>Powered by TB</span>
      </div>
    </header>
  );
}

const navbarStyle: React.CSSProperties = {
  background: "rgba(255, 255, 255, 0.96)",
  borderBottom: `1px solid ${theme.colors.border}`,
  padding: "14px 28px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: "18px",
  boxShadow: "0 10px 26px rgba(15, 23, 42, 0.05)",
  position: "sticky",
  top: 0,
  zIndex: 5,
};

const leftSectionStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  flexDirection: "row-reverse",
  gap: "14px",
};

const toggleButtonStyle: React.CSSProperties = {
  border: `1px solid ${theme.colors.border}`,
  background: "#f8fafc",
  color: theme.colors.primaryDark,
  borderRadius: "8px",
  padding: "8px 13px",
  cursor: "pointer",
  fontSize: "13px",
  fontWeight: 700,
};

const titleStyle: React.CSSProperties = {
  color: theme.colors.textPrimary,
  fontSize: "16px",
  fontWeight: 900,
};

const subtitleStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "12px",
  marginTop: "2px",
};

const brandStyle: React.CSSProperties = {
  fontSize: "13px",
  color: theme.colors.primaryDark,
  fontWeight: 800,
  whiteSpace: "nowrap",
};

const rightSectionStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "16px",
  flexWrap: "wrap",
  justifyContent: "flex-start",
};

const contextBlockStyle: React.CSSProperties = {
  display: "flex",
  gap: "10px",
  flexWrap: "wrap",
  justifyContent: "flex-end",
};

const contextItemStyle: React.CSSProperties = {
  fontSize: "12px",
  color: "#475569",
  fontWeight: 700,
  whiteSpace: "nowrap",
  background: "#f8fafc",
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "999px",
  padding: "5px 9px",
};

export default Navbar;
