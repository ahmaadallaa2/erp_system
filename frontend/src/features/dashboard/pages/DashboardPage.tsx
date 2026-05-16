import { useEffect, useMemo, useState } from "react";
import {
  ComparisonBar,
  ErrorMessage,
  LoadingState,
  MetricCard,
  PageHeader,
  ProgressBar,
  SectionCard,
  formatNumber,
} from "../../../components/ui/mvp";
import { theme } from "../../../styles/theme";
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

  const metrics = useMemo(() => {
    const totalSales = toNumber(summary?.total_sales);
    const totalPurchases = toNumber(summary?.total_purchases);
    const receivables = toNumber(summary?.customers_receivable);
    const payables = toNumber(summary?.suppliers_payable);
    const inventoryQuantity = toNumber(summary?.inventory_quantity);
    const inventoryItems = toNumber(summary?.inventory_items);
    const lowStockProducts = toNumber(summary?.low_stock_products);

    return {
      totalSales,
      totalPurchases,
      grossDifference: totalSales - totalPurchases,
      receivables,
      payables,
      inventoryQuantity,
      inventoryItems,
      lowStockProducts,
    };
  }, [summary]);

  return (
    <main style={pageStyle}>
      <PageHeader
        title="Management Dashboard"
        subtitle="A quick operating view of sales, purchases, inventory, and working balances."
      />

      <ErrorMessage message={error || ""} />
      {isLoading && <LoadingState label="Loading dashboard summary..." />}

      {!isLoading && !error && (
        <>
          <div style={kpiGridStyle}>
            <MetricCard
              title="Total Sales"
              value={formatNumber(metrics.totalSales)}
              subtitle="Posted sales invoices"
              tone="success"
            />
            <MetricCard
              title="Total Purchases"
              value={formatNumber(metrics.totalPurchases)}
              subtitle="Posted purchase invoices"
              tone="info"
            />
            <MetricCard
              title="Gross Difference"
              value={formatNumber(metrics.grossDifference)}
              subtitle="Sales minus purchases"
              tone={metrics.grossDifference >= 0 ? "success" : "danger"}
            />
            <MetricCard
              title="Inventory Quantity"
              value={formatNumber(metrics.inventoryQuantity)}
              subtitle={`${formatNumber(metrics.inventoryItems)} stocked items`}
              tone="neutral"
            />
            <MetricCard
              title="Customer Receivables"
              value={formatNumber(metrics.receivables)}
              subtitle="Open customer balance"
              tone="warning"
            />
            <MetricCard
              title="Supplier Payables"
              value={formatNumber(metrics.payables)}
              subtitle="Open supplier balance"
              tone="danger"
            />
            <MetricCard
              title="Low Stock Products"
              value={formatNumber(metrics.lowStockProducts)}
              subtitle="At or below reorder point"
              tone={metrics.lowStockProducts > 0 ? "warning" : "success"}
            />
          </div>

          <div style={visualGridStyle}>
            <SectionCard
              title="Sales vs Purchases"
              subtitle="Posted document totals from the dashboard summary."
            >
              <ComparisonBar
                label="Trading activity"
                leftLabel="Sales"
                leftValue={metrics.totalSales}
                rightLabel="Purchases"
                rightValue={metrics.totalPurchases}
              />
            </SectionCard>

            <SectionCard
              title="Receivables vs Payables"
              subtitle="Open business balances for customers and suppliers."
            >
              <ComparisonBar
                label="Working balance"
                leftLabel="Receivables"
                leftValue={metrics.receivables}
                rightLabel="Payables"
                rightValue={metrics.payables}
              />
            </SectionCard>
          </div>

          <div style={visualGridStyle}>
            <SectionCard
              title="Inventory Health"
              subtitle="Uses existing inventory quantity and low stock counts."
            >
              <div style={inventoryHealthStyle}>
                <ProgressBar
                  label="Products above low-stock alert"
                  value={Math.max(metrics.inventoryItems - metrics.lowStockProducts, 0)}
                  max={Math.max(metrics.inventoryItems, 1)}
                  tone="success"
                />
                <ProgressBar
                  label="Low-stock share"
                  value={metrics.lowStockProducts}
                  max={Math.max(metrics.inventoryItems, 1)}
                  tone={metrics.lowStockProducts > 0 ? "warning" : "success"}
                />
              </div>
            </SectionCard>

            <SectionCard title="Low Stock Alert">
              <div style={alertCardStyle(metrics.lowStockProducts > 0)}>
                <div style={alertNumberStyle}>{formatNumber(metrics.lowStockProducts)}</div>
                <div>
                  <strong>
                    {metrics.lowStockProducts > 0
                      ? "Products need attention"
                      : "No low-stock products"}
                  </strong>
                  <p style={alertTextStyle}>
                    {metrics.lowStockProducts > 0
                      ? "Review reorder points and replenish priority inventory."
                      : "Inventory is currently above configured reorder points."}
                  </p>
                </div>
              </div>
            </SectionCard>
          </div>
        </>
      )}
    </main>
  );
}

function toNumber(value: number | string | undefined | null) {
  const numeric = Number(value || 0);
  return Number.isFinite(numeric) ? numeric : 0;
}

const pageStyle: React.CSSProperties = {
  background: theme.colors.background,
  minHeight: "100%",
};

const kpiGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
  gap: "16px",
  marginBottom: "20px",
};

const visualGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
  gap: "20px",
};

const inventoryHealthStyle: React.CSSProperties = {
  display: "grid",
  gap: "18px",
};

function alertCardStyle(hasAlert: boolean): React.CSSProperties {
  return {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "18px",
    borderRadius: "8px",
    border: `1px solid ${hasAlert ? "rgba(245, 158, 11, 0.25)" : "rgba(22, 163, 74, 0.20)"}`,
    background: hasAlert ? "rgba(245, 158, 11, 0.08)" : "rgba(22, 163, 74, 0.08)",
  };
}

const alertNumberStyle: React.CSSProperties = {
  width: "58px",
  height: "58px",
  borderRadius: "8px",
  background: "#fff",
  border: `1px solid ${theme.colors.border}`,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: theme.colors.textPrimary,
  fontSize: "24px",
  fontWeight: 900,
};

const alertTextStyle: React.CSSProperties = {
  margin: "6px 0 0",
  color: theme.colors.textSecondary,
  fontSize: "13px",
};

export default DashboardPage;
