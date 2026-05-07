import { useEffect, useState } from "react";
import { Link } from "react-router";
import { listSalesInvoices } from "../api/list-sales-invoices";
import type { SalesInvoice } from "../types/sales-invoice";
import { listCustomers } from "../../partners/api/list-customers";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Partner } from "../../partners/types/partner";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { theme } from "../../../styles/theme";

function SalesInvoicesPage() {
  const [invoices, setInvoices] = useState<SalesInvoice[]>([]);
  const [customersMap, setCustomersMap] = useState<Record<string, string>>({});
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadInvoices() {
      try {
        setLoading(true);
        setError("");

        const [invoicesData, customersData, warehousesData] =
          await Promise.all([
            listSalesInvoices(),
            listCustomers(),
            listWarehouses(),
          ]);

        setInvoices(Array.isArray(invoicesData) ? invoicesData : []);

        const nextCustomersMap: Record<string, string> = {};
        (Array.isArray(customersData) ? customersData : []).forEach(
          (customer: Partner) => {
            nextCustomersMap[customer.id] = customer.name;
          }
        );
        setCustomersMap(nextCustomersMap);

        const nextWarehousesMap: Record<string, string> = {};
        (Array.isArray(warehousesData) ? warehousesData : []).forEach(
          (warehouse: Warehouse) => {
            nextWarehousesMap[warehouse.id] = warehouse.name;
          }
        );
        setWarehousesMap(nextWarehousesMap);
      } catch (err) {
        console.error("Sales invoices error:", err);
        setError("Failed to load sales invoices.");
      } finally {
        setLoading(false);
      }
    }

    loadInvoices();
  }, []);

  return (
    <main style={pageStyle}>
      <div style={headerStyle}>
        <div>
          <h1 style={titleStyle}>Sales Invoices</h1>
          <p style={subtitleStyle}>Manage customer sales invoices.</p>
        </div>

        <Link to="/sales-invoices/new" style={createLinkStyle}>
          + New Invoice
        </Link>
      </div>

      {loading && <p style={stateTextStyle}>Loading sales invoices...</p>}

      {!loading && error && <p style={errorTextStyle}>{error}</p>}

      {!loading && !error && invoices.length === 0 && (
        <div style={emptyStateStyle}>
          <h3 style={emptyStateTitleStyle}>No sales invoices found</h3>
          <p style={emptyStateTextStyle}>
            Start by creating your first sales invoice.
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
                  <th style={thStyle}>Customer</th>
                  <th style={thStyle}>Warehouse</th>
                  <th style={thStyle}>Date</th>
                  <th style={thStyle}>Status</th>
                  <th style={{ ...thStyle, textAlign: "right" }}>Total</th>
                  <th style={{ ...thStyle, textAlign: "center" }}>Items</th>
                </tr>
              </thead>

              <tbody>
                {invoices.map((invoice, index) => (
                  <tr key={invoice.id} style={getRowStyle(index)}>
                    <td style={tdStyle}>
                      <Link
                        to={`/sales-invoices/${invoice.id}`}
                        style={invoiceLinkStyle}
                      >
                        {invoice.invoice_number}
                      </Link>
                    </td>

                    <td style={tdStyle}>
                      <div style={primaryCellTextStyle}>
                        {customersMap[invoice.customer] || invoice.customer}
                      </div>
                    </td>

                    <td style={tdStyle}>
                      {warehousesMap[invoice.warehouse] || invoice.warehouse}
                    </td>

                    <td style={tdStyle}>
                      <span style={mutedTextStyle}>{invoice.date}</span>
                    </td>

                    <td style={tdStyle}>
                      <span style={statusBadgeStyle(invoice.status)}>
                        {invoice.status}
                      </span>
                    </td>

                    <td style={{ ...tdStyle, textAlign: "right" }}>
                      <span style={amountTextStyle}>
                        {invoice.total_amount}
                      </span>
                    </td>

                    <td style={{ ...tdStyle, textAlign: "center" }}>
                      <span style={countBadgeStyle}>
                        {invoice.items.length}
                      </span>
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

/* ===== Styles (نفس الـ Purchase) ===== */

const pageStyle: React.CSSProperties = {
  background: theme.colors.background,
};

const headerStyle: React.CSSProperties = {
  marginBottom: "24px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  flexWrap: "wrap",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "28px",
  fontWeight: 700,
};

const subtitleStyle: React.CSSProperties = {
  marginTop: "8px",
  color: theme.colors.textSecondary,
};

const createLinkStyle: React.CSSProperties = {
  background: theme.colors.primary,
  color: "#fff",
  padding: "10px 16px",
  borderRadius: "10px",
  textDecoration: "none",
  fontWeight: 700,
};

const tableCardStyle: React.CSSProperties = {
  background: "#fff",
  borderRadius: "16px",
  border: `1px solid ${theme.colors.border}`,
  overflow: "hidden",
};

const tableHeaderBarStyle: React.CSSProperties = {
  padding: "18px 20px",
  borderBottom: `1px solid ${theme.colors.border}`,
};

const tableTitleStyle: React.CSSProperties = {
  margin: 0,
};

const tableSubtitleStyle: React.CSSProperties = {
  fontSize: "13px",
  color: theme.colors.textSecondary,
};

const tableWrapperStyle: React.CSSProperties = {
  overflowX: "auto",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "separate",
};

const tableHeadRowStyle: React.CSSProperties = {
  background: "#f8fafc",
};

const thStyle: React.CSSProperties = {
  padding: "14px",
  fontSize: "13px",
  fontWeight: 700,
  textAlign: "left",
};

const tdStyle: React.CSSProperties = {
  padding: "14px",
};

function getRowStyle(index: number) {
  return {
    background: index % 2 === 0 ? "#fff" : "#f9fafb",
  };
}

const invoiceLinkStyle: React.CSSProperties = {
  color: theme.colors.primary,
  fontWeight: 700,
  textDecoration: "none",
};

const primaryCellTextStyle: React.CSSProperties = {
  fontWeight: 600,
};

const mutedTextStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
};

const amountTextStyle: React.CSSProperties = {
  fontWeight: 700,
};

const countBadgeStyle: React.CSSProperties = {
  background: "#e0f2fe",
  padding: "4px 10px",
  borderRadius: "999px",
  fontWeight: 700,
};

function statusBadgeStyle(status: string): React.CSSProperties {
  const isPosted = status === "posted";

  return {
    padding: "6px 12px",
    borderRadius: "999px",
    background: isPosted ? "#dcfce7" : "#fef3c7",
    color: isPosted ? "#166534" : "#92400e",
    fontWeight: 700,
    fontSize: "12px",
  };
}

const stateTextStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
};

const errorTextStyle: React.CSSProperties = {
  color: "red",
};

const emptyStateStyle: React.CSSProperties = {
  textAlign: "center",
  padding: "30px",
};

const emptyStateTitleStyle: React.CSSProperties = {
  margin: 0,
};

const emptyStateTextStyle: React.CSSProperties = {
  marginTop: "8px",
};

export default SalesInvoicesPage;