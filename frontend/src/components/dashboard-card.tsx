import { theme } from "../styles/theme";

type Props = {
  title: string;
  value: string;
  subtitle: string;
};

function DashboardCard({ title, value, subtitle }: Props) {
  return (
    <div style={cardStyle}>
      <h3 style={titleStyle}>{title}</h3>
      <p style={valueStyle}>{value}</p>
      <p style={subtitleStyle}>{subtitle}</p>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  position: "relative",
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "8px",
  padding: "18px",
  overflow: "hidden",
  cursor: "default",
  boxShadow: "0 8px 20px rgba(15, 23, 42, 0.04)",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "13px",
  color: theme.colors.textSecondary,
  fontWeight: 800,
};

const valueStyle: React.CSSProperties = {
  fontSize: "28px",
  fontWeight: 800,
  margin: "10px 0",
  color: theme.colors.textPrimary,
};

const subtitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "12px",
  color: theme.colors.textSecondary,
};

export default DashboardCard;
