import type { KeyboardEvent, ReactNode } from "react";
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

export function EmptyStateCard({
  title = "Data not available yet",
  message,
}: {
  title?: string;
  message?: string;
}) {
  return (
    <div style={emptyStateCardStyle}>
      <div style={emptyStateIconStyle}>i</div>
      <strong style={emptyStateCardTitleStyle}>{title}</strong>
      {message && <p style={emptyStateCardTextStyle}>{message}</p>}
    </div>
  );
}

export function SearchField({
  id,
  label = "Search",
  value,
  onChange,
  onSearch,
  onClear,
  placeholder,
}: {
  id: string;
  label?: string;
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  onClear: () => void;
  placeholder?: string;
}) {
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      onSearch();
    }
  }

  return (
    <div style={searchFieldGroupStyle}>
      <label style={searchFieldLabelStyle} htmlFor={id}>
        {label}
      </label>
      <div style={searchInputWrapStyle}>
        <input
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          style={searchInputStyle}
        />
        {value && (
          <button type="button" onClick={onClear} style={searchClearButtonStyle} aria-label="Clear search">
            x
          </button>
        )}
      </div>
    </div>
  );
}

export function ClearFiltersButton({
  onClick,
  label = "Clear",
}: {
  onClick: () => void;
  label?: string;
}) {
  return (
    <button type="button" onClick={onClick} style={clearFiltersButtonStyle}>
      {label}
    </button>
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
    <section className="erp-card-surface" style={sectionCardStyle}>
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
  accentColor,
}: {
  title: string;
  value: string;
  subtitle?: string;
  tone?: StatusTone;
  accentColor?: string;
}) {
  const palette = badgePalette[tone];
  const color = accentColor || palette.color;

  return (
    <div className="erp-card-surface erp-metric-card" style={{ ...metricCardStyle, borderTopColor: color }}>
      <div style={metricHeaderStyle}>
        <div style={metricTitleStyle}>{title}</div>
        <div
          style={{
            ...metricIconStyle,
            background: `${color}14`,
            borderColor: `${color}33`,
          }}
        >
          <span style={{ ...metricIconDotStyle, background: color }} />
        </div>
      </div>
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
    background: "#dcfce7",
    color: "#166534",
    border: "#bbf7d0",
  },
  warning: {
    background: "#fef3c7",
    color: "#92400e",
    border: "#fde68a",
  },
  danger: {
    background: "#fee2e2",
    color: "#991b1b",
    border: "#fecaca",
  },
  neutral: {
    background: "#f8fafc",
    color: "#475569",
    border: "#e2e8f0",
  },
  info: {
    background: "#ccfbf1",
    color: theme.colors.primaryDark,
    border: "#99f6e4",
  },
};

const pageHeaderStyle: React.CSSProperties = {
  marginBottom: "12px",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: "12px",
  flexWrap: "wrap",
  maxWidth: "100%",
  minWidth: 0,
};

const pageTitleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
  fontSize: "28px",
  fontWeight: 800,
  lineHeight: 1.15,
};

const pageSubtitleStyle: React.CSSProperties = {
  margin: "2px 0 0",
  color: theme.colors.textSecondary,
  fontSize: "12px",
  fontWeight: 400,
  lineHeight: 1.4,
};

const pageActionsStyle: React.CSSProperties = {
  display: "flex",
  gap: "8px",
  alignItems: "center",
  flexWrap: "wrap",
};

const noteStyle: React.CSSProperties = {
  marginTop: "8px",
  padding: "8px 10px",
  borderRadius: "10px",
  border: "1px solid #99f6e4",
  background: "rgba(236, 254, 255, 0.78)",
  color: theme.colors.primaryDark,
  fontSize: "13px",
  fontWeight: 700,
};

const badgeStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "26px",
  padding: "5px 10px",
  borderRadius: "999px",
  fontSize: "11px",
  fontWeight: 800,
  letterSpacing: "0.2px",
  whiteSpace: "nowrap",
};

const stateBoxStyle: React.CSSProperties = {
  background:
    "linear-gradient(145deg, rgba(255,255,255,0.90), rgba(236,254,255,0.54))",
  border: "1px solid rgba(255, 255, 255, 0.76)",
  borderRadius: "20px",
  padding: "16px 18px",
  color: theme.colors.textSecondary,
  fontSize: "14px",
  boxShadow:
    "0 24px 60px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255,255,255,0.88)",
  backdropFilter: "blur(22px) saturate(140%)",
};

const errorBoxStyle: React.CSSProperties = {
  marginBottom: "16px",
  padding: "12px 14px",
  borderRadius: "10px",
  border: "1px solid #fecaca",
  background: "#fef2f2",
  color: "#b91c1c",
  fontSize: "14px",
  whiteSpace: "pre-wrap",
};

const emptyStateStyle: React.CSSProperties = {
  background:
    "linear-gradient(145deg, rgba(255,255,255,0.88), rgba(248,250,252,0.72))",
  border: "1px dashed rgba(148, 163, 184, 0.48)",
  borderRadius: "20px",
  padding: "24px",
  textAlign: "center",
  boxShadow:
    "0 24px 64px rgba(15, 23, 42, 0.075), inset 0 1px 0 rgba(255,255,255,0.9)",
  backdropFilter: "blur(22px) saturate(140%)",
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
  background:
    "linear-gradient(145deg, rgba(255,255,255,0.92), rgba(236,254,255,0.42))",
  border: "1px solid rgba(255, 255, 255, 0.78)",
  borderRadius: "20px",
  padding: "18px",
  marginBottom: 0,
  boxShadow:
    "0 18px 42px rgba(15, 23, 42, 0.07), inset 0 1px 0 rgba(255,255,255,0.86)",
  maxWidth: "100%",
  minWidth: 0,
  boxSizing: "border-box",
  backdropFilter: "blur(24px) saturate(150%)",
  position: "relative",
  overflow: "hidden",
};

const sectionHeaderStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: "12px",
  marginBottom: "12px",
  maxWidth: "100%",
  minWidth: 0,
};

const sectionTitleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
  fontSize: "19px",
  fontWeight: 800,
};

const sectionSubtitleStyle: React.CSSProperties = {
  margin: "4px 0 0",
  color: theme.colors.textSecondary,
  fontSize: "13px",
};

const metricCardStyle: React.CSSProperties = {
  background:
    "linear-gradient(145deg, rgba(255,255,255,0.94), rgba(236,254,255,0.48))",
  border: "1px solid rgba(255, 255, 255, 0.82)",
  borderTop: "4px solid",
  borderRadius: "20px",
  padding: "16px",
  boxShadow:
    "0 18px 42px rgba(15, 23, 42, 0.075), inset 0 1px 0 rgba(255,255,255,0.9)",
  maxWidth: "100%",
  minWidth: 0,
  boxSizing: "border-box",
  backdropFilter: "blur(24px) saturate(150%)",
  position: "relative",
  overflow: "hidden",
};

const metricHeaderStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: "14px",
};

const metricIconStyle: React.CSSProperties = {
  width: "38px",
  height: "38px",
  borderRadius: "16px",
  border: "1px solid",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  flexShrink: 0,
};

const metricIconDotStyle: React.CSSProperties = {
  width: "12px",
  height: "12px",
  borderRadius: "999px",
};

const metricTitleStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "13px",
  fontWeight: 800,
};

const metricValueStyle: React.CSSProperties = {
  marginTop: "10px",
  color: theme.colors.textPrimary,
  fontSize: "32px",
  fontWeight: 900,
  lineHeight: 1.1,
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
  height: "9px",
  background: "#e5edf5",
  borderRadius: "999px",
  overflow: "hidden",
};

const barFillStyle: React.CSSProperties = {
  height: "100%",
  borderRadius: "999px",
};

const emptyStateCardStyle: React.CSSProperties = {
  minHeight: "112px",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  gap: "8px",
  padding: "18px",
  borderRadius: "20px",
  border: "1px dashed rgba(148, 163, 184, 0.44)",
  background:
    "linear-gradient(145deg, rgba(248, 250, 252, 0.84), rgba(236, 254, 255, 0.50))",
  color: "#64748b",
  textAlign: "center",
  backdropFilter: "blur(18px) saturate(140%)",
};

const emptyStateIconStyle: React.CSSProperties = {
  width: "28px",
  height: "28px",
  borderRadius: "999px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: "#ECFEFF",
  color: "#0891B2",
  fontSize: "13px",
  fontWeight: 900,
};

const emptyStateCardTitleStyle: React.CSSProperties = {
  color: "#475569",
  fontSize: "13px",
};

const emptyStateCardTextStyle: React.CSSProperties = {
  margin: 0,
  color: "#94a3b8",
  fontSize: "12px",
  lineHeight: 1.5,
};

const searchFieldGroupStyle: React.CSSProperties = {
  display: "grid",
  gap: "6px",
  minWidth: 0,
};

const searchFieldLabelStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "12px",
  fontWeight: 700,
};

const searchInputWrapStyle: React.CSSProperties = {
  position: "relative",
  minWidth: 0,
};

const searchInputStyle: React.CSSProperties = {
  width: "100%",
  height: "38px",
  borderRadius: "10px",
  border: `1px solid ${theme.colors.border}`,
  background: "#ffffff",
  padding: "0 34px 0 11px",
  color: theme.colors.textPrimary,
  fontSize: "13px",
  boxSizing: "border-box",
};

const searchClearButtonStyle: React.CSSProperties = {
  position: "absolute",
  insetInlineEnd: "6px",
  top: "50%",
  transform: "translateY(-50%)",
  width: "24px",
  height: "24px",
  borderRadius: "8px",
  border: "none",
  background: "rgba(148, 163, 184, 0.14)",
  color: theme.colors.textSecondary,
  cursor: "pointer",
  fontSize: "12px",
  fontWeight: 800,
  lineHeight: 1,
};

const clearFiltersButtonStyle: React.CSSProperties = {
  height: "38px",
  alignSelf: "end",
  borderRadius: "10px",
  border: `1px solid ${theme.colors.border}`,
  background: "#ffffff",
  color: theme.colors.textSecondary,
  padding: "0 12px",
  fontSize: "12px",
  fontWeight: 800,
  cursor: "pointer",
  whiteSpace: "nowrap",
};
