import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { listSuppliers } from "../../partners/api/list-suppliers";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import { createPurchaseInvoice } from "../api/create-purchase-invoice";
import type { Partner } from "../../partners/types/partner";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { ErrorMessage, LoadingState, PageHeader } from "../../../components/ui/mvp";

function CreatePurchaseInvoicePage() {
  const navigate = useNavigate();

  const [suppliers, setSuppliers] = useState<Partner[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loadingLookups, setLoadingLookups] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [branch, setBranch] = useState("");
  const [supplier, setSupplier] = useState("");
  const [warehouse, setWarehouse] = useState("");
  const [invoiceDate, setInvoiceDate] = useState("");
  const [vendorBillNumber, setVendorBillNumber] = useState("");
  const [shippingCost, setShippingCost] = useState("0.00");
  const [clearanceCost, setClearanceCost] = useState("0.00");
  const [commissionPercentage, setCommissionPercentage] = useState("0.00");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    async function loadLookups() {
      try {
        setLoadingLookups(true);
        setError("");

        const [suppliersData, warehousesData] = await Promise.all([
          listSuppliers(),
          listWarehouses(),
        ]);

        const nextSuppliers = Array.isArray(suppliersData) ? suppliersData : [];
        const nextWarehouses = Array.isArray(warehousesData) ? warehousesData : [];

        setSuppliers(nextSuppliers);
        setWarehouses(nextWarehouses);

        if (nextSuppliers.length > 0) {
          setSupplier(nextSuppliers[0].id);
        }

        if (nextWarehouses.length > 0) {
          setWarehouse(nextWarehouses[0].id);
          setBranch(nextWarehouses[0].branch);
        }

        setInvoiceDate(new Date().toISOString().slice(0, 10));
      } catch (err) {
        console.error("Purchase invoice lookups error:", err);
        setError("Failed to load suppliers and warehouses.");
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

      const created = await createPurchaseInvoice({
        branch,
        supplier,
        warehouse,
        invoice_date: invoiceDate,
        vendor_bill_number: vendorBillNumber || undefined,
        shipping_cost: shippingCost,
        clearance_cost: clearanceCost,
        commission_percentage: commissionPercentage,
        notes,
      });

        navigate(`/purchase-invoices/${created.id}`);
    } catch (err: any) {
      console.error("Create purchase invoice error:", err);
      setError(
        err?.response?.data
          ? JSON.stringify(err.response.data)
          : "Failed to create purchase invoice."
      );
    } finally {
      setSaving(false);
    }
  };

  if (loadingLookups) {
    return <LoadingState label="Loading purchase invoice form data..." />;
  }

  return (
    <main>
      <PageHeader
        title="Create Purchase Invoice"
        subtitle="Create a draft supplier invoice."
      />

      <form onSubmit={handleSubmit} style={formCardStyle}>
        <div style={gridStyle}>
          <div>
            <label style={labelStyle}>Supplier</label>
            <select
              value={supplier}
              onChange={(e) => setSupplier(e.target.value)}
              style={inputStyle}
            >
              {suppliers.map((item) => (
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
              value={invoiceDate}
              onChange={(e) => setInvoiceDate(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>Vendor Bill Number</label>
            <input
              type="text"
              value={vendorBillNumber}
              onChange={(e) => setVendorBillNumber(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>Shipping Cost</label>
            <input
              type="text"
              value={shippingCost}
              onChange={(e) => setShippingCost(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>Clearance Cost</label>
            <input
              type="text"
              value={clearanceCost}
              onChange={(e) => setClearanceCost(e.target.value)}
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>Commission %</label>
            <input
              type="text"
              value={commissionPercentage}
              onChange={(e) => setCommissionPercentage(e.target.value)}
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

        <ErrorMessage message={error} />

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

export default CreatePurchaseInvoicePage;
