import { useEffect, useState } from "react";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  MetricCard,
  PageHeader,
  StatusBadge,
  formatNumber,
  toBusinessLabel,
} from "../../../components/ui/mvp";
import { theme } from "../../../styles/theme";
import { listPartners } from "../api/list-partners";
import type { Partner } from "../types/partner";

function PartnersPage() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadPartners() {
      try {
        setLoading(true);
        setError("");

        const data = await listPartners();
        setPartners(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Partners load error:", err);
        setError("Failed to load partners.");
      } finally {
        setLoading(false);
      }
    }

    loadPartners();
  }, []);

  const activeCount = partners.filter((partner) => partner.is_active).length;
  const customerCount = partners.filter((partner) =>
    partner.partner_type.includes("customer")
  ).length;
  const supplierCount = partners.filter((partner) =>
    partner.partner_type.includes("supplier")
  ).length;

  return (
    <main>
      <PageHeader
        title="Partners"
        subtitle="Customers, suppliers, and shared business contacts."
      />

      {loading && <LoadingState label="Loading partners..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && partners.length > 0 && (
        <div style={summaryGridStyle}>
          <MetricCard title="Total Partners" value={formatNumber(partners.length)} tone="info" />
          <MetricCard title="Active Partners" value={formatNumber(activeCount)} tone="success" />
          <MetricCard title="Customers" value={formatNumber(customerCount)} tone="neutral" />
          <MetricCard title="Suppliers" value={formatNumber(supplierCount)} tone="warning" />
        </div>
      )}

      {!loading && !error && partners.length === 0 && (
        <EmptyState
          title="No partners found"
          message="Create customers and suppliers from the partner workflow."
        />
      )}

      {!loading && !error && partners.length > 0 && (
        <div style={tableCardStyle}>
          <table style={tableStyle}>
            <thead style={tableHeadStyle}>
              <tr>
                <th style={thStyle}>Code</th>
                <th style={thStyle}>Name</th>
                <th style={thStyle}>Partner Type</th>
                <th style={thStyle}>Phone</th>
                <th style={thStyle}>Email</th>
                <th style={thStyle}>Status</th>
              </tr>
            </thead>
            <tbody>
              {partners.map((partner) => (
                <tr key={partner.id}>
                  <td style={tdStrongStyle}>{partner.code}</td>
                  <td style={tdStyle}>{partner.name}</td>
                  <td style={tdStyle}>
                    <StatusBadge status={toBusinessLabel(partner.partner_type)} tone="info" />
                  </td>
                  <td style={tdStyle}>{partner.phone || "-"}</td>
                  <td style={tdStyle}>{partner.email || "-"}</td>
                  <td style={tdStyle}>
                    <StatusBadge status={partner.is_active ? "active" : "inactive"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

const tableCardStyle: React.CSSProperties = {
  overflowX: "auto",
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "8px",
};

const summaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: "16px",
  marginBottom: "20px",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
};

const tableHeadStyle: React.CSSProperties = {
  background: "#f8fafc",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "12px 14px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "13px",
  color: theme.colors.textSecondary,
};

const tdStyle: React.CSSProperties = {
  padding: "13px 14px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "14px",
  color: theme.colors.textPrimary,
};

const tdStrongStyle: React.CSSProperties = {
  ...tdStyle,
  fontWeight: 800,
};

export default PartnersPage;
