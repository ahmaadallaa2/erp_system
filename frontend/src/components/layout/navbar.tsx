import { theme } from "../../styles/theme";

type NavbarProps = {
  onToggleSidebar: () => void;
};

function Navbar({ onToggleSidebar }: NavbarProps) {
  return (
    <header style={navbarStyle}>
      <div style={leftSectionStyle}>
        <button onClick={onToggleSidebar} style={toggleButtonStyle}>
          Menu
        </button>

        <div>
          <strong style={titleStyle}>TB ERP System</strong>
          <div style={subtitleStyle}>Internal operations workspace</div>
        </div>
      </div>

      <span style={brandStyle}>Powered by TB</span>
    </header>
  );
}

const navbarStyle: React.CSSProperties = {
  background: theme.colors.surface,
  borderBottom: `1px solid ${theme.colors.border}`,
  padding: "14px 24px",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  boxShadow: "0 1px 2px rgba(0, 0, 0, 0.04)",
};

const leftSectionStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "14px",
};

const toggleButtonStyle: React.CSSProperties = {
  border: `1px solid ${theme.colors.border}`,
  background: theme.colors.surface,
  color: theme.colors.primaryDark,
  borderRadius: "8px",
  padding: "8px 12px",
  cursor: "pointer",
  fontSize: "13px",
  fontWeight: 700,
};

const titleStyle: React.CSSProperties = {
  color: theme.colors.textPrimary,
  fontSize: "16px",
  fontWeight: 800,
};

const subtitleStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "12px",
  marginTop: "2px",
};

const brandStyle: React.CSSProperties = {
  fontSize: "13px",
  color: theme.colors.primaryDark,
  fontWeight: 700,
};

export default Navbar;
