import { useEffect, useState } from "react";
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

  return (
    <main>
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>Partners</h1>
        <p style={{ marginTop: "8px", color: "#666" }}>
          Manage customers and suppliers.
        </p>
      </div>

      {loading && <p>Loading partners...</p>}

      {!loading && error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && !error && partners.length === 0 && <p>No partners found.</p>}

      {!loading && !error && partners.length > 0 && (
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
                <th style={thStyle}>Phone</th>
                <th style={thStyle}>Email</th>
                <th style={thStyle}>Status</th>
              </tr>
            </thead>
            <tbody>
              {partners.map((partner) => (
                <tr key={partner.id}>
                  <td style={tdStyle}>{partner.code}</td>
                  <td style={tdStyle}>{partner.name}</td>
                  <td style={tdStyle}>{partner.partner_type}</td>
                  <td style={tdStyle}>{partner.phone || "-"}</td>
                  <td style={tdStyle}>{partner.email || "-"}</td>
                  <td style={tdStyle}>
                    {partner.is_active ? "Active" : "Inactive"}
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

export default PartnersPage;