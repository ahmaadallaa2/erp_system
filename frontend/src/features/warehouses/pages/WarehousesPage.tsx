import { useEffect, useState } from "react";
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
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>Warehouses</h1>
        <p style={{ marginTop: "8px", color: "#666" }}>
          Manage inventory warehouses.
        </p>
      </div>

      {loading && <p>Loading warehouses...</p>}

      {!loading && error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && !error && warehouses.length === 0 && (
        <p>No warehouses found.</p>
      )}

      {!loading && !error && warehouses.length > 0 && (
        <div
          style={{
            overflowX: "auto",
            background: "#fff",
            border: "1px solid #ddd",
            borderRadius: "8px",
          }}
        >
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
            }}
          >
            <thead style={{ background: "#f5f5f5" }}>
              <tr>
                <th style={thStyle}>Code</th>
                <th style={thStyle}>Name</th>
                <th style={thStyle}>Type</th>
                <th style={thStyle}>Address</th>
                <th style={thStyle}>Status</th>
              </tr>
            </thead>
            <tbody>
              {warehouses.map((warehouse) => (
                <tr key={warehouse.id}>
                  <td style={tdStyle}>{warehouse.code}</td>
                  <td style={tdStyle}>{warehouse.name}</td>
                  <td style={tdStyle}>{warehouse.warehouse_type}</td>
                  <td style={tdStyle}>{warehouse.address || "-"}</td>
                  <td style={tdStyle}>
                    {warehouse.is_active ? "Active" : "Inactive"}
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

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "12px",
  borderBottom: "1px solid #ddd",
  fontSize: "14px",
};

const tdStyle: React.CSSProperties = {
  padding: "12px",
  borderBottom: "1px solid #eee",
  fontSize: "14px",
};

export default WarehousesPage;