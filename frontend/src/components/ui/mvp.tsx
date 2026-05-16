import type { ReactNode } from "react";
import { theme } from "../../styles/theme";

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  note?: ReactNode;
};

export function PageHeader({ title, subtitle, actions, note }: PageHeaderProps) {
  return (
    <div style={pageHeaderStyle}>
      <div>
        <h1 style={pageTitleStyle}>{title}</h1>
        {subtitle && <p style={pageSubtitleStyle}>{subtitle}</p>}
        {note && <div style={noteStyle}>{note}</div>}
      </div>
      {actions && <div style={pageActionsStyle}>{actions}</div>}
    </div>
  );
}

type StatusBadgeProps = {
  status: string;
  tone?: StatusTone;
};

type StatusTone = "success" | "warning" | "danger" | "neutral" | "info";

export function StatusBadge({ status, tone }: StatusBadgeProps) {
  const resolvedTone = tone || getStatusTone(status);
  const palette = badgePalette[resolvedTone];

  return (
    <span
      style={{
        ...badgeStyle,
        background: palette.background,
        color: palette.color,
        border: `1px solid ${palette.border}`,
      }}
    >
      {toBusinessLabel(status)}
    </span>
  );
}

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <div style={stateBoxStyle}>{label}</div>;
}

export function ErrorMessage({ message }: { message: string }) {
  if (!message) return null;
  return <div style={errorBoxStyle}>{message}</div>;
}

export function EmptyState({
  title,
  message,
}: {
  title: string;
  message?: string;
}) {
  return (
    <div style={emptyStateStyle}>
      <h3 style={emptyTitleStyle}>{title}</h3>
      {message && <p style={emptyTextStyle}>{message}</p>}
    </div>
  );
}

export function SectionCard({
  title,
  subtitle,
  actions,
  children,
}: {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section style={sectionCardStyle}>
      {(title || actions) && (
        <div style={sectionHeaderStyle}>
          <div>
            {title && <h2 style={sectionTitleStyle}>{title}</h2>}
            {subtitle && <p style={sectionSubtitleStyle}>{subtitle}</p>}
          </div>
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function MetricCard({
  title,
  value,
  subtitle,
  tone = "neutral",
}: {
  title: string;
  value: string;
  subtitle?: string;
  tone?: StatusTone;
}) {
  const palette = badgePalette[tone];

  return (
    <div style={{ ...metricCardStyle, borderTopColor: palette.color }}>
      <div style={metricTitleStyle}>{title}</div>
      <div style={metricValueStyle}>{value}</div>
      {subtitle && <div style={metricSubtitleStyle}>{subtitle}</div>}
    </div>
  );
}

export function ComparisonBar({
  label,
  leftLabel,
  leftValue,
  rightLabel,
  rightValue,
}: {
  label: string;
  leftLabel: string;
  leftValue: number;
  rightLabel: string;
  rightValue: number;
}) {
  const max = Math.max(leftValue, rightValue, 1);
  const leftWidth = `${Math.max((leftValue / max) * 100, 3)}%`;
  const rightWidth = `${Math.max((rightValue / max) * 100, 3)}%`;

  return (
    <div>
      <div style={comparisonLabelStyle}>{label}</div>
      <div style={comparisonRowsStyle}>
        <BarRow label={leftLabel} value={leftValue} width={leftWidth} color={theme.colors.primary} />
        <BarRow label={rightLabel} value={rightValue} width={rightWidth} color="#64748b" />
      </div>
    </div>
  );
}

function BarRow({
  label,
  value,
  width,
  color,
}: {
  label: string;
  value: number;
  width: string;
  color: string;
}) {
  return (
    <div style={barRowStyle}>
      <div style={barMetaStyle}>
        <span>{label}</span>
        <strong>{formatNumber(value)}</strong>
      </div>
      <div style={barTrackStyle}>
        <div style={{ ...barFillStyle, width, background: color }} />
      </div>
    </div>
  );
}

export function ProgressBar({
  label,
  value,
  max,
  tone = "info",
}: {
  label: string;
  value: number;
  max: number;
  tone?: StatusTone;
}) {
  const palette = badgePalette[tone];
  const width = `${Math.min(Math.max((value / Math.max(max, 1)) * 100, 0), 100)}%`;

  return (
    <div>
      <div style={barMetaStyle}>
        <span>{label}</span>
        <strong>
          {formatNumber(value)} / {formatNumber(max)}
        </strong>
      </div>
      <div style={barTrackStyle}>
        <div style={{ ...barFillStyle, width, background: palette.color }} />
      </div>
    </div>
  );
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(value);
}

export function toBusinessLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getStatusTone(status: string): StatusTone {
  const normalized = status.toLowerCase();

  if (normalized === "posted" || normalized === "active") return "success";
  if (normalized === "cancelled" || normalized === "inactive") return "danger";
  if (normalized === "draft" || normalized === "pending") return "warning";
  return "neutral";
}

const badgePalette = {
  success: {
    background: "rgba(22, 163, 74, 0.10)",
    color: "#166534",
    border: "rgba(22, 163, 74, 0.20)",
  },
  warning: {
    background: "rgba(245, 158, 11, 0.12)",
    color: "#92400e",
    border: "rgba(245, 158, 11, 0.22)",
  },
  danger: {
    background: "rgba(220, 38, 38, 0.10)",
    color: "#991b1b",
    border: "rgba(220, 38, 38, 0.20)",
  },
  neutral: {
    background: "#f3f4f6",
    color: theme.colors.textSecondary,
    border: theme.colors.border,
  },
  info: {
    background: "rgba(14, 165, 164, 0.10)",
    color: theme.colors.primaryDark,
    border: "rgba(14, 165, 164, 0.20)",
  },
};

const pageHeaderStyle: React.CSSProperties = {
  marginBottom: "24px",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: "16px",
  flexWrap: "wrap",
};

const pageTitleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
  fontSize: "28px",
  fontWeight: 800,
};

const pageSubtitleStyle: React.CSSProperties = {
  margin: "8px 0 0",
  color: theme.colors.textSecondary,
  fontSize: "14px",
};

const pageActionsStyle: React.CSSProperties = {
  display: "flex",
  gap: "10px",
  alignItems: "center",
  flexWrap: "wrap",
};

const noteStyle: React.CSSProperties = {
  marginTop: "12px",
  padding: "10px 12px",
  borderRadius: "8px",
  border: `1px solid rgba(14, 165, 164, 0.22)`,
  background: "rgba(14, 165, 164, 0.08)",
  color: theme.colors.primaryDark,
  fontSize: "13px",
  fontWeight: 600,
};

const badgeStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "24px",
  padding: "4px 10px",
  borderRadius: "999px",
  fontSize: "12px",
  fontWeight: 800,
  whiteSpace: "nowrap",
};

const stateBoxStyle: React.CSSProperties = {
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "8px",
  padding: "18px",
  color: theme.colors.textSecondary,
  fontSize: "14px",
};

const errorBoxStyle: React.CSSProperties = {
  marginBottom: "16px",
  padding: "12px",
  borderRadius: "8px",
  border: "1px solid rgba(220, 38, 38, 0.20)",
  background: "#fef2f2",
  color: "#b91c1c",
  fontSize: "14px",
  whiteSpace: "pre-wrap",
};

const emptyStateStyle: React.CSSProperties = {
  background: theme.colors.surface,
  border: `1px dashed ${theme.colors.border}`,
  borderRadius: "8px",
  padding: "30px",
  textAlign: "center",
};

const emptyTitleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
  fontSize: "17px",
};

const emptyTextStyle: React.CSSProperties = {
  margin: "8px 0 0",
  color: theme.colors.textSecondary,
  fontSize: "14px",
};

const sectionCardStyle: React.CSSProperties = {
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "8px",
  padding: "20px",
  marginBottom: "20px",
  boxShadow: "0 10px 28px rgba(15, 23, 42, 0.04)",
};

const sectionHeaderStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: "12px",
  marginBottom: "16px",
};

const sectionTitleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
  fontSize: "18px",
};

const sectionSubtitleStyle: React.CSSProperties = {
  margin: "6px 0 0",
  color: theme.colors.textSecondary,
  fontSize: "13px",
};

const metricCardStyle: React.CSSProperties = {
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderTop: "4px solid",
  borderRadius: "8px",
  padding: "16px",
  boxShadow: "0 10px 24px rgba(15, 23, 42, 0.04)",
};

const metricTitleStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "13px",
  fontWeight: 800,
};

const metricValueStyle: React.CSSProperties = {
  marginTop: "8px",
  color: theme.colors.textPrimary,
  fontSize: "26px",
  fontWeight: 900,
  fontVariantNumeric: "tabular-nums",
};

const metricSubtitleStyle: React.CSSProperties = {
  marginTop: "6px",
  color: theme.colors.textSecondary,
  fontSize: "12px",
};

const comparisonLabelStyle: React.CSSProperties = {
  marginBottom: "14px",
  color: theme.colors.textPrimary,
  fontWeight: 800,
};

const comparisonRowsStyle: React.CSSProperties = {
  display: "grid",
  gap: "14px",
};

const barRowStyle: React.CSSProperties = {
  display: "grid",
  gap: "8px",
};

const barMetaStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: "12px",
  color: theme.colors.textSecondary,
  fontSize: "13px",
};

const barTrackStyle: React.CSSProperties = {
  height: "10px",
  background: "#eef2f7",
  borderRadius: "999px",
  overflow: "hidden",
};

const barFillStyle: React.CSSProperties = {
  height: "100%",
  borderRadius: "999px",
};
