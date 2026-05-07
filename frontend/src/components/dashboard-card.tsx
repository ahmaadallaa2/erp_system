import { theme } from "../styles/theme";

type Props = {
  title: string;
  value: string;
  subtitle: string;
};

function DashboardCard({ title, value, subtitle }: Props) {
  return (
    <div style={cardStyle}>
      <div style={accentBar} />
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
  borderRadius: "12px",
  padding: "16px",
  overflow: "hidden",
  cursor: "default",
};

const accentBar: React.CSSProperties = {
  position: "absolute",
  top: 0,
  left: 0,
  width: "100%",
  height: "4px",
  background: theme.colors.primary,
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "13px",
  color: theme.colors.textSecondary,
};

const valueStyle: React.CSSProperties = {
  fontSize: "28px",
  fontWeight: "bold",
  margin: "10px 0",
  color: theme.colors.primary,
};

const subtitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "12px",
  color: theme.colors.textSecondary,
};

export default DashboardCard;