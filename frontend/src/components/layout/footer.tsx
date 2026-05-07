import { theme } from "../../styles/theme";

function Footer() {
  return (
    <footer style={footerStyle}>
      <span>TB ERP System</span>
      <span style={versionStyle}>Frontend MVP</span>
    </footer>
  );
}

const footerStyle: React.CSSProperties = {
  background: theme.colors.surface,
  borderTop: `1px solid ${theme.colors.border}`,
  padding: "14px 24px",
  fontSize: "14px",
  color: theme.colors.textSecondary,
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
};

const versionStyle: React.CSSProperties = {
  color: theme.colors.primary,
  fontWeight: 600,
};

export default Footer;