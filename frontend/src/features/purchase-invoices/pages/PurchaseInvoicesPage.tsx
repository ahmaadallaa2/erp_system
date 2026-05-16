import { useEffect, useState } from "react";
import { Link } from "react-router";
import { listPurchaseInvoices } from "../api/list-purchase-invoices";
import type { PurchaseInvoice } from "../types/purchase-invoice";
import { listSuppliers } from "../../partners/api/list-suppliers";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Partner } from "../../partners/types/partner";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { theme } from "../../../styles/theme";
import { MetricCard, StatusBadge, formatNumber } from "../../../components/ui/mvp";

function PurchaseInvoicesPage() {
  const [invoices, setInvoices] = useState<PurchaseInvoice[]>([]);
  const [suppliersMap, setSuppliersMap] = useState<Record<string, string>>({});
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadInvoices() {
      try {
        setLoading(true);
        setError("");

        const [invoicesData, suppliersData, warehousesData] = await Promise.all([
          listPurchaseInvoices(),
          listSuppliers(),
          listWarehouses(),
        ]);

        setInvoices(Array.isArray(invoicesData) ? invoicesData : []);

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
      } catch (err) {
        console.error("Purchase invoices error:", err);
        setError("Failed to load purchase invoices.");
      } finally {
        setLoading(false);
      }
    }

    loadInvoices();
  }, []);

  const totalAmount = invoices.reduce(
    (total, invoice) => total + Number(invoice.total_amount || 0),
    0
  );
  const postedCount = invoices.filter((invoice) => invoice.status === "posted").length;
  const draftCount = invoices.filter((invoice) => invoice.status === "draft").length;

  return (
    <main style={pageStyle}>
      <div style={headerStyle}>
        <div>
          <h1 style={titleStyle}>Purchase Invoices</h1>
          <p style={subtitleStyle}>Manage supplier purchase invoices.</p>
        </div>

        <Link to="/purchase-invoices/new" style={createLinkStyle}>
          + New Invoice
        </Link>
      </div>

      {loading && <p style={stateTextStyle}>Loading purchase invoices...</p>}

      {!loading && error && <p style={errorTextStyle}>{error}</p>}

      {!loading && !error && invoices.length > 0 && (
        <div style={summaryGridStyle}>
          <MetricCard
            title="Purchase Total"
            value={formatNumber(totalAmount)}
            subtitle="All loaded purchase invoices"
            tone="info"
          />
          <MetricCard
            title="Posted Invoices"
            value={formatNumber(postedCount)}
            subtitle="Completed supplier documents"
            tone="success"
          />
          <MetricCard
            title="Draft Invoices"
            value={formatNumber(draftCount)}
            subtitle="Waiting to be posted"
            tone="warning"
          />
        </div>
      )}

      {!loading && !error && invoices.length === 0 && (
        <div style={emptyStateStyle}>
          <h3 style={emptyStateTitleStyle}>No purchase invoices found</h3>
          <p style={emptyStateTextStyle}>
            Start by creating your first purchase invoice.
          </p>
        </div>
      )}

      {!loading && !error && invoices.length > 0 && (
        <div style={tableCardStyle}>
          <div style={tableHeaderBarStyle}>
            <div>
              <h2 style={tableTitleStyle}>Invoices List</h2>
              <p style={tableSubtitleStyle}>
                Total invoices: {invoices.length}
              </p>
            </div>
          </div>

          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead>
                <tr style={tableHeadRowStyle}>
                  <th style={{ ...thStyle, minWidth: "160px" }}>Invoice No.</th>
                  <th style={thStyle}>Supplier</th>
                  <th style={thStyle}>Warehouse</th>
                  <th style={thStyle}>Date</th>
                  <th style={thStyle}>Status</th>
                  <th style={{ ...thStyle, textAlign: "right" }}>Total</th>
                  <th style={{ ...thStyle, textAlign: "center" }}>Items Count</th>
                </tr>
              </thead>

              <tbody>
                {invoices.map((invoice, index) => (
                  <tr
                    key={invoice.id}
                    style={getRowStyle(index)}
                  >
                    <td style={tdStyle}>
                      <Link
                        to={`/purchase-invoices/${invoice.id}`}
                        style={invoiceLinkStyle}
                      >
                        {invoice.invoice_number}
                      </Link>
                    </td>

                    <td style={tdStyle}>
                      <div style={primaryCellTextStyle}>
                        {suppliersMap[invoice.supplier] || invoice.supplier}
                      </div>
                    </td>

                    <td style={tdStyle}>
                      <div style={secondaryCellTextStyle}>
                        {warehousesMap[invoice.warehouse] || invoice.warehouse}
                      </div>
                    </td>

                    <td style={tdStyle}>
                      <span style={mutedTextStyle}>{invoice.invoice_date}</span>
                    </td>

                    <td style={tdStyle}>
                      <StatusBadge status={invoice.status} />
                    </td>

                    <td style={{ ...tdStyle, textAlign: "right" }}>
                      <span style={amountTextStyle}>{invoice.total_amount}</span>
                    </td>

                    <td style={{ ...tdStyle, textAlign: "center" }}>
                      <span style={countBadgeStyle}>{invoice.items.length}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}

const pageStyle: React.CSSProperties = {
  background: theme.colors.background,
};

const headerStyle: React.CSSProperties = {
  marginBottom: "24px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: "16px",
  flexWrap: "wrap",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
  fontSize: "28px",
  fontWeight: 700,
};

const subtitleStyle: React.CSSProperties = {
  marginTop: "8px",
  color: theme.colors.textSecondary,
  fontSize: "14px",
};

const createLinkStyle: React.CSSProperties = {
  textDecoration: "none",
  background: theme.colors.primary,
  color: "#ffffff",
  padding: "10px 16px",
  borderRadius: "10px",
  fontWeight: 700,
  fontSize: "14px",
  whiteSpace: "nowrap",
  boxShadow: "0 8px 20px rgba(14, 165, 164, 0.18)",
};

const summaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "16px",
  marginBottom: "20px",
};

const tableCardStyle: React.CSSProperties = {
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "16px",
  overflow: "hidden",
  boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
};

const tableHeaderBarStyle: React.CSSProperties = {
  padding: "18px 20px",
  borderBottom: `1px solid ${theme.colors.border}`,
  background: "linear-gradient(180deg, rgba(14,165,164,0.04), rgba(14,165,164,0.01))",
};

const tableTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "18px",
  color: theme.colors.textPrimary,
};

const tableSubtitleStyle: React.CSSProperties = {
  margin: "6px 0 0",
  fontSize: "13px",
  color: theme.colors.textSecondary,
};

const tableWrapperStyle: React.CSSProperties = {
  overflowX: "auto",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "separate",
  borderSpacing: 0,
};

const tableHeadRowStyle: React.CSSProperties = {
  background: "#f8fafc",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "14px 16px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "13px",
  fontWeight: 700,
  color: theme.colors.textSecondary,
  letterSpacing: "0.2px",
  whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
  padding: "16px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "14px",
  color: theme.colors.textPrimary,
  verticalAlign: "middle",
};

function getRowStyle(index: number): React.CSSProperties {
  return {
    background: index % 2 === 0 ? "#ffffff" : "#fbfdff",
    transition: "background 0.2s ease",
  };
}

const invoiceLinkStyle: React.CSSProperties = {
  color: theme.colors.primaryDark,
  textDecoration: "none",
  fontWeight: 700,
};

const primaryCellTextStyle: React.CSSProperties = {
  color: theme.colors.textPrimary,
  fontWeight: 600,
};

const secondaryCellTextStyle: React.CSSProperties = {
  color: theme.colors.textPrimary,
};

const mutedTextStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontWeight: 500,
};

const amountTextStyle: React.CSSProperties = {
  color: theme.colors.textPrimary,
  fontWeight: 700,
  fontVariantNumeric: "tabular-nums",
};

const countBadgeStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  minWidth: "30px",
  height: "30px",
  padding: "0 10px",
  borderRadius: "999px",
  background: "rgba(14, 165, 164, 0.10)",
  color: theme.colors.primaryDark,
  fontWeight: 700,
  fontSize: "13px",
};

const stateTextStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "14px",
};

const errorTextStyle: React.CSSProperties = {
  color: theme.colors.danger,
  fontSize: "14px",
};

const emptyStateStyle: React.CSSProperties = {
  background: theme.colors.surface,
  border: `1px dashed ${theme.colors.border}`,
  borderRadius: "16px",
  padding: "32px",
  textAlign: "center",
};

const emptyStateTitleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
  fontSize: "18px",
};

const emptyStateTextStyle: React.CSSProperties = {
  marginTop: "8px",
  color: theme.colors.textSecondary,
  fontSize: "14px",
};

export default PurchaseInvoicesPage;
