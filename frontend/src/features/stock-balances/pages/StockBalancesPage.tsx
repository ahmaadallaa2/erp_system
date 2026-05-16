import { useEffect, useState } from "react";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  MetricCard,
  PageHeader,
  StatusBadge,
  formatNumber,
} from "../../../components/ui/mvp";
import { theme } from "../../../styles/theme";
import { listProducts } from "../../products/api/list-products";
import type { Product } from "../../products/types/product";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { listStockBalances } from "../api/list-stock-balances";
import type { StockBalance } from "../types/stock-balance";

function StockBalancesPage() {
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadBalances() {
      try {
        setLoading(true);
        setError("");

        const [balancesData, productsData, warehousesData] = await Promise.all([
          listStockBalances(),
          listProducts(),
          listWarehouses(),
        ]);

        setBalances(Array.isArray(balancesData) ? balancesData : []);

        const nextProductsMap: Record<string, string> = {};
        (Array.isArray(productsData) ? productsData : []).forEach((product: Product) => {
          nextProductsMap[product.id] = product.name;
        });
        setProductsMap(nextProductsMap);

        const nextWarehousesMap: Record<string, string> = {};
        (Array.isArray(warehousesData) ? warehousesData : []).forEach(
          (warehouse: Warehouse) => {
            nextWarehousesMap[warehouse.id] = warehouse.name;
          }
        );
        setWarehousesMap(nextWarehousesMap);
      } catch (err) {
        console.error("Stock balances error:", err);
        setError("Failed to load stock balances.");
      } finally {
        setLoading(false);
      }
    }

    loadBalances();
  }, []);

  const totalQuantity = balances.reduce(
    (total, balance) => total + Number(balance.quantity || 0),
    0
  );
  const totalAvailable = balances.reduce(
    (total, balance) => total + Number(balance.available_quantity || 0),
    0
  );
  const lowStockCount = balances.filter(
    (balance) => Number(balance.available_quantity) <= Number(balance.reorder_point)
  ).length;

  return (
    <main>
      <PageHeader title="Stock Balances" subtitle="Current stock by product and warehouse." />

      {loading && <LoadingState label="Loading stock balances..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && balances.length > 0 && (
        <div style={summaryGridStyle}>
          <MetricCard title="Balance Rows" value={formatNumber(balances.length)} tone="info" />
          <MetricCard title="Total Quantity" value={formatNumber(totalQuantity)} tone="neutral" />
          <MetricCard title="Available Quantity" value={formatNumber(totalAvailable)} tone="success" />
          <MetricCard
            title="Low Stock Rows"
            value={formatNumber(lowStockCount)}
            tone={lowStockCount > 0 ? "warning" : "success"}
          />
        </div>
      )}

      {!loading && !error && balances.length === 0 && (
        <EmptyState
          title="No stock balances found"
          message="Stock balances appear after posted stock activity."
        />
      )}

      {!loading && !error && balances.length > 0 && (
        <div style={tableCardStyle}>
          <table style={tableStyle}>
            <thead style={tableHeadStyle}>
              <tr>
                <th style={thStyle}>Product</th>
                <th style={thStyle}>Warehouse</th>
                <th style={rightThStyle}>Quantity</th>
                <th style={rightThStyle}>Reserved</th>
                <th style={rightThStyle}>Available</th>
                <th style={rightThStyle}>Reorder Point</th>
                <th style={thStyle}>Stock Health</th>
              </tr>
            </thead>
            <tbody>
              {balances.map((balance) => {
                const isLowStock =
                  Number(balance.available_quantity) <= Number(balance.reorder_point);

                return (
                  <tr key={balance.id} style={isLowStock ? lowStockRowStyle : undefined}>
                    <td style={tdStyle}>{productsMap[balance.product] || balance.product}</td>
                    <td style={tdStyle}>
                      {warehousesMap[balance.warehouse] || balance.warehouse}
                    </td>
                    <td style={rightTdStyle}>{balance.quantity}</td>
                    <td style={rightTdStyle}>{balance.reserved_quantity}</td>
                    <td style={rightTdStyle}>{balance.available_quantity}</td>
                    <td style={rightTdStyle}>{balance.reorder_point}</td>
                    <td style={tdStyle}>
                      <StatusBadge
                        status={isLowStock ? "Low Stock" : "Available"}
                        tone={isLowStock ? "warning" : "success"}
                      />
                    </td>
                  </tr>
                );
              })}
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

const rightThStyle: React.CSSProperties = {
  ...thStyle,
  textAlign: "right",
};

const tdStyle: React.CSSProperties = {
  padding: "13px 14px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "14px",
  color: theme.colors.textPrimary,
};

const rightTdStyle: React.CSSProperties = {
  ...tdStyle,
  textAlign: "right",
  fontVariantNumeric: "tabular-nums",
};

const lowStockRowStyle: React.CSSProperties = {
  background: "rgba(245, 158, 11, 0.06)",
};

export default StockBalancesPage;
