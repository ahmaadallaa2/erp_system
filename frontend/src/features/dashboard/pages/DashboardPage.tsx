import { useEffect, useState } from "react";
import { theme } from "../../../styles/theme";
import DashboardCard from "../../../components/dashboard-card";
import { getDashboardSummary } from "../api/dashboard-api";
import type { DashboardSummary } from "../api/dashboard-api";

function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      setIsLoading(true);
      setError(null);

      try {
        const data = await getDashboardSummary();
        setSummary(data);
      } catch (err) {
        console.error("Dashboard error:", err);
        setError("Unable to load dashboard summary.");
      } finally {
        setIsLoading(false);
      }
    }

    loadStats();
  }, []);

  return (
    <main style={pageStyle}>
      <div style={headerStyle}>
        <h1 style={titleStyle}>Dashboard</h1>
        <p style={subtitleStyle}>Overview of your system.</p>
      </div>

      {error && <p style={errorStyle}>{error}</p>}

      <div style={gridStyle}>
        <DashboardCard
          title="Total Sales"
          value={formatMetric(summary?.total_sales, isLoading)}
          subtitle="Posted sales invoices"
        />

        <DashboardCard
          title="Total Purchases"
          value={formatMetric(summary?.total_purchases, isLoading)}
          subtitle="Posted purchase invoices"
        />

        <DashboardCard
          title="Inventory Items"
          value={formatMetric(summary?.inventory_items, isLoading)}
          subtitle="Products with stock balances"
        />

        <DashboardCard
          title="Inventory Quantity"
          value={formatMetric(summary?.inventory_quantity, isLoading)}
          subtitle="Current stock quantity"
        />

        <DashboardCard
          title="Customers Receivable"
          value={formatMetric(summary?.customers_receivable, isLoading)}
          subtitle="Sales minus inbound payments"
        />

        <DashboardCard
          title="Suppliers Payable"
          value={formatMetric(summary?.suppliers_payable, isLoading)}
          subtitle="Purchases minus outbound payments"
        />

        <DashboardCard
          title="Low Stock Products"
          value={formatMetric(summary?.low_stock_products, isLoading)}
          subtitle="Rows at or below reorder point"
        />
      </div>
    </main>
  );
}

function formatMetric(value: number | string | undefined, isLoading: boolean) {
  if (isLoading) {
    return "...";
  }

  if (value === undefined || value === null || value === "") {
    return "0";
  }

  return String(value);
}

const pageStyle: React.CSSProperties = {
  background: theme.colors.background,
  minHeight: "100%",
};

const headerStyle: React.CSSProperties = {
  marginBottom: "24px",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
};

const subtitleStyle: React.CSSProperties = {
  marginTop: "8px",
  color: theme.colors.textSecondary,
};

const errorStyle: React.CSSProperties = {
  margin: "0 0 16px",
  color: theme.colors.danger,
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
  gap: "16px",
};

export default DashboardPage;
