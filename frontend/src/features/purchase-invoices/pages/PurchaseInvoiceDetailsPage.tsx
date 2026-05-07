import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { getPurchaseInvoice } from "../api/get-purchase-invoice";
import { createPurchaseInvoiceItem } from "../api/create-purchase-invoice-item";
import { postPurchaseInvoice } from "../api/post-purchase-invoice";
import type { PurchaseInvoice } from "../types/purchase-invoice";
import { listSuppliers } from "../../partners/api/list-suppliers";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import { listProducts } from "../../products/api/list-products";
import type { Partner } from "../../partners/types/partner";
import type { Warehouse } from "../../warehouses/types/warehouse";
import type { Product } from "../../products/types/product";

function PurchaseInvoiceDetailsPage() {
  const { id } = useParams();

  const [invoice, setInvoice] = useState<PurchaseInvoice | null>(null);
  const [suppliersMap, setSuppliersMap] = useState<Record<string, string>>({});
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingItem, setSavingItem] = useState(false);
  const [itemError, setItemError] = useState("");
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState("");

  const [product, setProduct] = useState("");
  const [quantity, setQuantity] = useState("1.00");
  const [unitPrice, setUnitPrice] = useState("0.00");
  const [itemNotes, setItemNotes] = useState("");

  async function loadInvoiceData(invoiceId: string) {
    const [invoiceData, suppliersData, warehousesData, productsData] =
      await Promise.all([
        getPurchaseInvoice(invoiceId),
        listSuppliers(),
        listWarehouses(),
        listProducts(),
      ]);

    setInvoice(invoiceData);

    const nextSuppliersMap: Record<string, string> = {};
    (Array.isArray(suppliersData) ? suppliersData : []).forEach(
      (supplier: Partner) => {
        nextSuppliersMap[supplier.id] = supplier.name;
      }
    );
    setSuppliersMap(nextSuppliersMap);

    const nextWarehousesMap: Record<string, string> = {};
    (Array.isArray(warehousesData) ? warehousesData : []).forEach(
      (warehouse: Warehouse) => {
        nextWarehousesMap[warehouse.id] = warehouse.name;
      }
    );
    setWarehousesMap(nextWarehousesMap);

    const nextProducts = Array.isArray(productsData) ? productsData : [];
    setProducts(nextProducts);

    const nextProductsMap: Record<string, string> = {};
    nextProducts.forEach((item: Product) => {
      nextProductsMap[item.id] = item.name;
    });
    setProductsMap(nextProductsMap);

    if (nextProducts.length > 0 && !product) {
      setProduct(nextProducts[0].id);
      setUnitPrice(nextProducts[0].cost_price || "0.00");
    }
  }

  useEffect(() => {
    async function run() {
      if (!id) {
        setError("Invoice ID is missing.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");
        await loadInvoiceData(id);
      } catch (err) {
        console.error("Purchase invoice details error:", err);
        setError("Failed to load purchase invoice details.");
      } finally {
        setLoading(false);
      }
    }

    run();
  }, [id]);

  const handleProductChange = (productId: string) => {
    setProduct(productId);
    setItemError("");

    const selectedProduct = products.find((item) => item.id === productId);
    if (selectedProduct) {
      setUnitPrice(selectedProduct.cost_price || "0.00");
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!id) return;

    if (!product) {
      setItemError("Please select a product.");
      return;
    }

    if (Number(quantity) <= 0 || Number.isNaN(Number(quantity))) {
      setItemError("Quantity must be greater than zero.");
      return;
    }

    if (Number(unitPrice) <= 0 || Number.isNaN(Number(unitPrice))) {
      setItemError("Unit price must be greater than zero.");
      return;
    }

    try {
      setSavingItem(true);
      setItemError("");

      await createPurchaseInvoiceItem({
        invoice: id,
        product,
        quantity,
        unit_price: unitPrice,
        notes: itemNotes || undefined,
      });

      await loadInvoiceData(id);

      setQuantity("1.00");
      setItemNotes("");
    } catch (err: any) {
      console.error("Add invoice item error:", err);
      setItemError(
        err?.response?.data
          ? JSON.stringify(err.response.data)
          : "Failed to add invoice item."
      );
    } finally {
      setSavingItem(false);
    }
  };

  const handlePostInvoice = async () => {
    if (!id || !invoice) return;

    if (invoice.items.length === 0) {
      setPostError("You cannot post an invoice without items.");
      return;
    }

    const confirmPost = window.confirm(
      "Are you sure you want to post this invoice? This action cannot be undone."
    );

    if (!confirmPost) return;

    try {
      setPosting(true);
      setPostError("");

      await postPurchaseInvoice(id);
      await loadInvoiceData(id);
    } catch (err: any) {
      console.error("Post invoice error:", err);
      setPostError(
        err?.response?.data
          ? JSON.stringify(err.response.data)
          : "Failed to post invoice."
      );
    } finally {
      setPosting(false);
    }
  };

  if (loading) {
    return <p>Loading purchase invoice...</p>;
  }

  if (error) {
    return <p style={{ color: "red" }}>{error}</p>;
  }

  if (!invoice) {
    return <p>Invoice not found.</p>;
  }

  const isPosted = invoice.status === "posted";
  const addItemDisabled =
    savingItem ||
    !product ||
    Number(quantity) <= 0 ||
    Number.isNaN(Number(quantity)) ||
    Number(unitPrice) <= 0 ||
    Number.isNaN(Number(unitPrice));

  return (
    <main>
      <div style={headerWrapperStyle}>
        <div>
          <h1 style={{ margin: 0 }}>{invoice.invoice_number}</h1>
          <p style={{ marginTop: "8px", color: "#666" }}>
            Purchase invoice details
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {!isPosted && (
            <button
              type="button"
              onClick={handlePostInvoice}
              disabled={posting}
              style={{
                ...postButtonStyle,
                opacity: posting ? 0.7 : 1,
                cursor: posting ? "not-allowed" : "pointer",
              }}
            >
              {posting ? "Posting..." : "Post Invoice"}
            </button>
          )}

          <div style={statusBadgeStyle(invoice.status)}>{invoice.status}</div>
        </div>
      </div>

      {postError && <div style={errorBoxStyle}>{postError}</div>}

      <div style={sectionCardStyle}>
        <h2 style={sectionTitleStyle}>Invoice Information</h2>

        <div style={infoGridStyle}>
          <InfoRow
            label="Supplier"
            value={suppliersMap[invoice.supplier] || invoice.supplier}
          />
          <InfoRow
            label="Warehouse"
            value={warehousesMap[invoice.warehouse] || invoice.warehouse}
          />
          <InfoRow label="Invoice Date" value={invoice.invoice_date} />
          <InfoRow
            label="Vendor Bill No."
            value={invoice.vendor_bill_number || "-"}
          />
          <InfoRow label="Total Amount" value={invoice.total_amount} />
          <InfoRow label="Shipping Cost" value={invoice.shipping_cost} />
          <InfoRow label="Clearance Cost" value={invoice.clearance_cost} />
          <InfoRow
            label="Commission %"
            value={invoice.commission_percentage}
          />
        </div>

        <div style={{ marginTop: "16px" }}>
          <strong>Notes:</strong>
          <p style={{ marginTop: "8px", color: "#444" }}>
            {invoice.notes || "-"}
          </p>
        </div>
      </div>

      {!isPosted && (
        <div style={sectionCardStyle}>
          <h2 style={sectionTitleStyle}>Add Item</h2>

          <form onSubmit={handleAddItem}>
            <div style={infoGridStyle}>
              <div>
                <label style={labelStyle}>Product</label>
                <select
                  value={product}
                  onChange={(e) => handleProductChange(e.target.value)}
                  style={inputStyle}
                >
                  {products.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={labelStyle}>Quantity</label>
                <input
                  type="text"
                  value={quantity}
                  onChange={(e) => {
                    setQuantity(e.target.value);
                    setItemError("");
                  }}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Unit Price</label>
                <input
                  type="text"
                  value={unitPrice}
                  onChange={(e) => {
                    setUnitPrice(e.target.value);
                    setItemError("");
                  }}
                  style={inputStyle}
                />
              </div>
            </div>

            <div style={{ marginTop: "16px" }}>
              <label style={labelStyle}>Notes</label>
              <textarea
                value={itemNotes}
                onChange={(e) => setItemNotes(e.target.value)}
                style={{ ...inputStyle, minHeight: "90px", resize: "vertical" }}
              />
            </div>

            {itemError && <div style={errorBoxStyle}>{itemError}</div>}

            <div style={{ marginTop: "16px" }}>
              <button
                type="submit"
                disabled={addItemDisabled}
                style={{
                  ...buttonStyle,
                  opacity: addItemDisabled ? 0.7 : 1,
                  cursor: addItemDisabled ? "not-allowed" : "pointer",
                }}
              >
                {savingItem ? "Adding..." : "Add Item"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div style={sectionCardStyle}>
        <h2 style={sectionTitleStyle}>Invoice Items</h2>

        {invoice.items.length === 0 ? (
          <p>No items added yet.</p>
        ) : (
          <div
            style={{
              overflowX: "auto",
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
                  <th style={thStyle}>Product</th>
                  <th style={thStyle}>Quantity</th>
                  <th style={thStyle}>Unit Price</th>
                  <th style={thStyle}>Line Total</th>
                  <th style={thStyle}>Notes</th>
                </tr>
              </thead>
              <tbody>
                {invoice.items.map((item) => (
                  <tr key={item.id}>
                    <td style={tdStyle}>
                      {productsMap[item.product] || item.product}
                    </td>
                    <td style={tdStyle}>{item.quantity}</td>
                    <td style={tdStyle}>{item.unit_price}</td>
                    <td style={tdStyle}>{item.line_total}</td>
                    <td style={tdStyle}>{item.notes || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}

type InfoRowProps = {
  label: string;
  value: string;
};

function InfoRow({ label, value }: InfoRowProps) {
  return (
    <div>
      <div style={{ fontSize: "13px", color: "#666", marginBottom: "6px" }}>
        {label}
      </div>
      <div style={{ fontWeight: 600 }}>{value}</div>
    </div>
  );
}

const headerWrapperStyle: React.CSSProperties = {
  marginBottom: "20px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "16px",
};

const sectionCardStyle: React.CSSProperties = {
  background: "#fff",
  border: "1px solid #ddd",
  borderRadius: "12px",
  padding: "20px",
  marginBottom: "20px",
};

const sectionTitleStyle: React.CSSProperties = {
  marginTop: 0,
  marginBottom: "16px",
};

const infoGridStyle: React.CSSProperties = {
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
  fontWeight: 600,
};

const postButtonStyle: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: "8px",
  border: "none",
  background: "#16a34a",
  color: "#fff",
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

function statusBadgeStyle(status: string): React.CSSProperties {
  return {
    padding: "8px 12px",
    borderRadius: "999px",
    background: status === "posted" ? "#dcfce7" : "#fef3c7",
    color: status === "posted" ? "#166534" : "#92400e",
    fontWeight: 700,
    textTransform: "capitalize",
    fontSize: "13px",
  };
}

export default PurchaseInvoiceDetailsPage;