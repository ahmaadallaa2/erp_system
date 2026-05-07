import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { listCustomers } from "../../partners/api/list-customers";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import { createSalesInvoice } from "../api/create-sales-invoice";
import type { Partner } from "../../partners/types/partner";
import type { Warehouse } from "../../warehouses/types/warehouse";

function CreateSalesInvoicePage() {
  const navigate = useNavigate();

  const [customers, setCustomers] = useState<Partner[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [branch, setBranch] = useState("");
  const [customer, setCustomer] = useState("");
  const [warehouse, setWarehouse] = useState("");
  const [date, setDate] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    async function loadLookups() {
      try {
        setLoadingLookups(true);
        setError("");

        const [customersData, warehousesData] = await Promise.all([
          listCustomers(),
          listWarehouses(),
        ]);

        const nextCustomers = Array.isArray(customersData) ? customersData : [];
        const nextWarehouses = Array.isArray(warehousesData) ? warehousesData : [];

        setCustomers(nextCustomers);
        setWarehouses(nextWarehouses);

        if (nextCustomers.length > 0) {
          setCustomer(nextCustomers[0].id);
        }

        if (nextWarehouses.length > 0) {
          setWarehouse(nextWarehouses[0].id);
          setBranch(nextWarehouses[0].branch);
        }

        setDate(new Date().toISOString().slice(0, 10));
      } catch (err) {
        console.error("Sales invoice lookups error:", err);
        setError("Failed to load customers and warehouses.");
      } finally {
        setLoadingLookups(false);
      }
    }

    loadLookups();
  }, []);

  const handleWarehouseChange = (warehouseId: string) => {
    setWarehouse(warehouseId);

    const selectedWarehouse = warehouses.find((item) => item.id === warehouseId);
    if (selectedWarehouse) {
      setBranch(selectedWarehouse.branch);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setSaving(true);
      setError("");

      const created = await createSalesInvoice({
        branch,
        customer,
        warehouse,
        date,
        notes,
      });

      navigate(`/sales-invoices/${created.id}`);
    } catch (err: any) {
      console.error("Create sales invoice error:", err);
      setError(
        err?.response?.data
          ? JSON.stringify(err.response.data)
          : "Failed to create sales invoice."
      );
    } finally {
      setSaving(false);
    }
  };

  if (loadingLookups) {
    return <p>Loading form data...</p>;
  }

  return (
    <main>
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>Create Sales Invoice</h1>
        <p style={{ marginTop: "8px", color: "#666" }}>
          Create a draft customer invoice.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={formCardStyle}>
        <div style={gridStyle}>
          <div>
            <label style={labelStyle}>Customer</label>
            <select
              value={customer}
              onChange={(e) => setCustomer(e.target.value)}
              style={inputStyle}
            >
              {customers.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={labelStyle}>Warehouse</label>
            <select
              value={warehouse}
              onChange={(e) => handleWarehouseChange(e.target.value)}
              style={inputStyle}
            >
              {warehouses.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={labelStyle}>Invoice Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              style={inputStyle}
            />
          </div>
        </div>

        <div style={{ marginTop: "16px" }}>
          <label style={labelStyle}>Notes</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            style={{ ...inputStyle, minHeight: "100px", resize: "vertical" }}
          />
        </div>

        {error && <div style={errorBoxStyle}>{error}</div>}

        <div style={{ marginTop: "20px" }}>
          <button type="submit" disabled={saving} style={buttonStyle}>
            {saving ? "Saving..." : "Create Invoice"}
          </button>
        </div>
      </form>
    </main>
  );
}

const formCardStyle: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #ddd",
  borderRadius: "12px",
  padding: "20px",
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "16px",
};

const labelStyle: React.CSSProperties = {
  display: "block",
  marginBottom: "8px",
  fontSize: "14px",
  fontWeight: 600,
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "8px",
  border: "1px solid #d1d5db",
  fontSize: "14px",
  boxSizing: "border-box",
};

const buttonStyle: React.CSSProperties = {
  padding: "10px 16px",
  border: "none",
  borderRadius: "8px",
  background: "#111827",
  color: "#fff",
  cursor: "pointer",
  fontWeight: 600,
};

const errorBoxStyle: React.CSSProperties = {
  marginTop: "16px",
  padding: "12px",
  borderRadius: "8px",
  background: "#fef2f2",
  color: "#b91c1c",
  fontSize: "14px",
  whiteSpace: "pre-wrap",
};

export default CreateSalesInvoicePage;