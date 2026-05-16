import { useEffect, useState } from "react";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
  StatusBadge,
  toBusinessLabel,
} from "../../../components/ui/mvp";
import { theme } from "../../../styles/theme";
import { listWarehouses } from "../api/list-warehouses";
import type { Warehouse } from "../types/warehouse";

function WarehousesPage() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadWarehouses() {
      try {
        setLoading(true);
        setError("");

        const result = await listWarehouses();
        setWarehouses(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error("Warehouses load error:", err);
        setError("Failed to load warehouses.");
      } finally {
        setLoading(false);
      }
    }

    loadWarehouses();
  }, []);

  return (
    <main>
      <PageHeader
        title="Warehouses"
        subtitle="Storage locations and branches used by inventory documents."
      />

      {loading && <LoadingState label="Loading warehouses..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && warehouses.length === 0 && (
        <EmptyState title="No warehouses found" message="Warehouses will appear here once created." />
      )}

      {!loading && !error && warehouses.length > 0 && (
        <div style={tableCardStyle}>
          <table style={tableStyle}>
            <thead style={tableHeadStyle}>
              <tr>
                <th style={thStyle}>Code</th>
                <th style={thStyle}>Warehouse Name</th>
                <th style={thStyle}>Type</th>
                <th style={thStyle}>Branch</th>
                <th style={thStyle}>Address</th>
                <th style={thStyle}>Status</th>
              </tr>
            </thead>
            <tbody>
              {warehouses.map((warehouse) => (
                <tr key={warehouse.id}>
                  <td style={tdStrongStyle}>{warehouse.code}</td>
                  <td style={tdStyle}>{warehouse.name}</td>
                  <td style={tdStyle}>{toBusinessLabel(warehouse.warehouse_type)}</td>
                  <td style={tdStyle}>{warehouse.branch || "-"}</td>
                  <td style={tdStyle}>{warehouse.address || "-"}</td>
                  <td style={tdStyle}>
                    <StatusBadge status={warehouse.is_active ? "active" : "inactive"} />
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

export default WarehousesPage;
