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
import { listProducts } from "../api/list-products";
import type { Product } from "../types/product";

function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProducts() {
      try {
        setLoading(true);
        setError("");

        const result = await listProducts();
        setProducts(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error("Products load error:", err);
        setError("Failed to load products.");
      } finally {
        setLoading(false);
      }
    }

    loadProducts();
  }, []);

  const activeCount = products.filter((product) => product.is_active).length;
  const serviceCount = products.filter((product) => product.product_type === "service").length;
  const stockCount = products.length - serviceCount;

  return (
    <main>
      <PageHeader
        title="Products"
        subtitle="Inventory and service items used by purchase and sales invoices."
      />

      {loading && <LoadingState label="Loading products..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && products.length > 0 && (
        <div style={summaryGridStyle}>
          <MetricCard title="Total Products" value={formatNumber(products.length)} tone="info" />
          <MetricCard title="Active Items" value={formatNumber(activeCount)} tone="success" />
          <MetricCard title="Stock Items" value={formatNumber(stockCount)} tone="neutral" />
          <MetricCard title="Service Items" value={formatNumber(serviceCount)} tone="warning" />
        </div>
      )}

      {!loading && !error && products.length === 0 && (
        <EmptyState title="No products found" message="Products will appear here once created." />
      )}

      {!loading && !error && products.length > 0 && (
        <div style={tableCardStyle}>
          <table style={tableStyle}>
            <thead style={tableHeadStyle}>
              <tr>
                <th style={thStyle}>SKU</th>
                <th style={thStyle}>Product Name</th>
                <th style={thStyle}>Type</th>
                <th style={rightThStyle}>Cost Price</th>
                <th style={rightThStyle}>Sale Price</th>
                <th style={rightThStyle}>Reorder Point</th>
                <th style={thStyle}>Status</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id}>
                  <td style={tdStrongStyle}>{product.sku}</td>
                  <td style={tdStyle}>{product.name}</td>
                  <td style={tdStyle}>{toBusinessLabel(product.product_type)}</td>
                  <td style={rightTdStyle}>{product.cost_price}</td>
                  <td style={rightTdStyle}>{product.sale_price}</td>
                  <td style={rightTdStyle}>{product.reorder_point}</td>
                  <td style={tdStyle}>
                    <StatusBadge status={product.is_active ? "active" : "inactive"} />
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

const tdStrongStyle: React.CSSProperties = {
  ...tdStyle,
  fontWeight: 800,
};

const rightTdStyle: React.CSSProperties = {
  ...tdStyle,
  textAlign: "right",
  fontVariantNumeric: "tabular-nums",
};

export default ProductsPage;
