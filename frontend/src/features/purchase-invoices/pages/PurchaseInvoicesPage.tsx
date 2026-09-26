import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import {
  EmptyState,
  ErrorMessage,
  ClearFiltersButton,
  LoadingState,
  MetricCard,
  PageHeader,
  SearchField,
  StatusBadge,
  formatNumber,
} from "../../../components/ui/mvp";
import { getApiErrorMessage } from "../../../lib/api/errors";
import { theme } from "../../../styles/theme";
import { listSuppliers } from "../../partners/api/list-suppliers";
import type { Partner } from "../../partners/types/partner";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { listPurchaseInvoices } from "../api/list-purchase-invoices";
import { postPurchaseInvoice } from "../api/post-purchase-invoice";
import type { PurchaseInvoice } from "../types/purchase-invoice";

type StatusFilter = "all" | "draft" | "posted";
const searchStorageKey = "erp.purchase-invoices.search";

function PurchaseInvoicesPage() {
  const [invoices, setInvoices] = useState<PurchaseInvoice[]>([]);
  const [suppliersMap, setSuppliersMap] = useState<Record<string, string>>({});
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [postingId, setPostingId] = useState<string | null>(null);
  const [query, setQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [draftQuery, setDraftQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

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
      (Array.isArray(suppliersData) ? suppliersData : []).forEach((supplier: Partner) => {
        nextSuppliersMap[supplier.id] = supplier.name;
      });
      setSuppliersMap(nextSuppliersMap);

      const nextWarehousesMap: Record<string, string> = {};
      (Array.isArray(warehousesData) ? warehousesData : []).forEach((warehouse: Warehouse) => {
        nextWarehousesMap[warehouse.id] = warehouse.name;
      });
      setWarehousesMap(nextWarehousesMap);
    } catch (err) {
      console.error("Purchase invoices error:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInvoices();
  }, []);

  const filteredInvoices = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return invoices.filter((invoice) => {
      const supplierName = suppliersMap[invoice.supplier] || invoice.supplier;
      const matchesQuery =
        !normalizedQuery ||
        invoice.invoice_number.toLowerCase().includes(normalizedQuery) ||
        supplierName.toLowerCase().includes(normalizedQuery);
      const matchesStatus = statusFilter === "all" || invoice.status === statusFilter;

      return matchesQuery && matchesStatus;
    });
  }, [invoices, query, statusFilter, suppliersMap]);

  const totalAmount = filteredInvoices.reduce(
    (total, invoice) => total + Number(invoice.total_amount || 0),
    0
  );
  const postedCount = filteredInvoices.filter((invoice) => invoice.status === "posted").length;
  const draftCount = filteredInvoices.filter((invoice) => invoice.status === "draft").length;

  async function handlePostInvoice(id: string) {
    try {
      setPostingId(id);
      setError("");
      await postPurchaseInvoice(id);
      await loadInvoices();
    } catch (err) {
      console.error("Post purchase invoice error:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setPostingId(null);
    }
  }

  function applySearch() {
    const nextQuery = draftQuery.trim();
    setQuery(nextQuery);
    sessionStorage.setItem(searchStorageKey, nextQuery);
  }

  function clearFilters() {
    setDraftQuery("");
    setQuery("");
    setStatusFilter("all");
    sessionStorage.removeItem(searchStorageKey);
  }

  return (
    <main style={pageStyle}>
      <PageHeader
        title="Purchase Invoices"
        subtitle="Operational workspace for supplier purchase invoices."
        actions={
          <Link to="/purchase-invoices/new" style={createLinkStyle}>
            New Invoice
          </Link>
        }
      />

      <ErrorMessage message={error} />
      {loading && <LoadingState label="Loading purchase invoices..." />}

      {!loading && (
        <div style={workspaceStyle}>
          <section style={summaryGridStyle}>
            <MetricCard
              title="Purchases Total"
              value={formatNumber(totalAmount)}
              subtitle="Filtered purchase invoices"
              tone="info"
            />
            <MetricCard
              title="Posted Purchases"
              value={formatNumber(postedCount)}
              subtitle="Completed supplier documents"
              tone="success"
            />
            <MetricCard
              title="Draft Purchases"
              value={formatNumber(draftCount)}
              subtitle="Waiting to be posted"
              tone="warning"
            />
          </section>

          <section style={tableCardStyle}>
            <div style={filtersBarStyle}>
              <SearchField
                id="purchase-search"
                value={draftQuery}
                onChange={setDraftQuery}
                onSearch={applySearch}
                onClear={clearFilters}
                placeholder="Invoice number or supplier"
              />

              <div style={filterGroupStyle}>
                <label style={filterLabelStyle} htmlFor="purchase-status">
                  Status
                </label>
                <select
                  id="purchase-status"
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
                  style={selectStyle}
                >
                  <option value="all">All</option>
                  <option value="draft">Draft</option>
                  <option value="posted">Posted</option>
                </select>
              </div>

              <div style={filterGroupStyle}>
                <label style={filterLabelStyle}>Date range</label>
                <div style={datePlaceholderStyle}>Ready when API supports date filtering</div>
              </div>

              <div style={tableMetaStyle}>
                <strong>{filteredInvoices.length}</strong>
                <span>of {invoices.length} invoices</span>
              </div>

              <ClearFiltersButton onClick={clearFilters} />
            </div>

            {filteredInvoices.length === 0 ? (
              <div style={emptyWrapStyle}>
                <EmptyState
                  title="No purchase invoices found"
                  message="Adjust filters or create a new purchase invoice."
                />
              </div>
            ) : (
              <>
                <div style={tableWrapperStyle}>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        <th style={{ ...thStyle, minWidth: "150px" }}>Invoice No.</th>
                        <th style={thStyle}>Supplier</th>
                        <th style={thStyle}>Warehouse</th>
                        <th style={thStyle}>Date</th>
                        <th style={thStyle}>Status</th>
                        <th style={{ ...thStyle, textAlign: "end" }}>Total</th>
                        <th style={{ ...thStyle, textAlign: "center" }}>Items</th>
                        <th style={{ ...thStyle, textAlign: "center", minWidth: "210px" }}>Actions</th>
                      </tr>
                    </thead>

                    <tbody>
                      {filteredInvoices.map((invoice) => (
                        <tr key={invoice.id}>
                          <td style={tdStyle}>
                            <Link to={`/purchase-invoices/${invoice.id}`} style={invoiceLinkStyle}>
                              {invoice.invoice_number}
                            </Link>
                          </td>
                          <td style={tdStyle}>
                            <strong style={primaryCellTextStyle}>
                              {suppliersMap[invoice.supplier] || invoice.supplier}
                            </strong>
                          </td>
                          <td style={tdStyle}>{warehousesMap[invoice.warehouse] || invoice.warehouse}</td>
                          <td style={tdStyle}>
                            <span style={mutedTextStyle}>{invoice.invoice_date}</span>
                          </td>
                          <td style={tdStyle}>
                            <StatusBadge status={invoice.status} />
                          </td>
                          <td style={{ ...tdStyle, textAlign: "end" }}>
                            <span style={amountTextStyle}>{invoice.total_amount}</span>
                          </td>
                          <td style={{ ...tdStyle, textAlign: "center" }}>
                            <span style={countBadgeStyle}>{invoice.items.length}</span>
                          </td>
                          <td style={{ ...tdStyle, textAlign: "center" }}>
                            <div style={actionsStyle}>
                              <Link to={`/purchase-invoices/${invoice.id}`} style={actionLinkStyle}>
                                View
                              </Link>
                              {invoice.status === "draft" && (
                                <button
                                  type="button"
                                  onClick={() => handlePostInvoice(invoice.id)}
                                  disabled={postingId === invoice.id}
                                  style={{
                                    ...actionButtonStyle,
                                    opacity: postingId === invoice.id ? 0.65 : 1,
                                    cursor: postingId === invoice.id ? "not-allowed" : "pointer",
                                  }}
                                >
                                  {postingId === invoice.id ? "Posting..." : "Post"}
                                </button>
                              )}
                              {invoice.journal_entry && (
                                <Link
                                  to={`/accounting/journal-entries/${invoice.journal_entry}`}
                                  style={actionLinkStyle}
                                >
                                  Journal
                                </Link>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={tableFooterStyle}>
                  <span>Pagination UI ready when backend returns paged purchase invoice results.</span>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

const pageStyle: React.CSSProperties = {
  background: "transparent",
  minHeight: "100%",
  minWidth: 0,
};

const workspaceStyle: React.CSSProperties = {
  display: "grid",
  gap: "16px",
};

const createLinkStyle: React.CSSProperties = {
  background: theme.colors.primary,
  color: "#fff",
  padding: "9px 14px",
  borderRadius: "10px",
  textDecoration: "none",
  fontWeight: 700,
  fontSize: "13px",
};

const summaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "14px",
};

const tableCardStyle: React.CSSProperties = {
  background: "linear-gradient(145deg, rgba(255,255,255,0.94), rgba(236,254,255,0.38))",
  borderRadius: "20px",
  border: "1px solid rgba(255, 255, 255, 0.78)",
  overflow: "hidden",
  boxShadow: "0 18px 42px rgba(15, 23, 42, 0.07), inset 0 1px 0 rgba(255,255,255,0.86)",
  backdropFilter: "blur(22px) saturate(145%)",
  minWidth: 0,
};

const filtersBarStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(220px, 1.5fr) minmax(140px, 0.7fr) minmax(220px, 1fr) auto auto",
  gap: "12px",
  alignItems: "end",
  padding: "14px 16px",
  borderBottom: `1px solid ${theme.colors.border}`,
};

const filterGroupStyle: React.CSSProperties = {
  display: "grid",
  gap: "6px",
  minWidth: 0,
};

const filterLabelStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "12px",
  fontWeight: 700,
};

const inputStyle: React.CSSProperties = {
  height: "38px",
  borderRadius: "10px",
  border: `1px solid ${theme.colors.border}`,
  background: "#ffffff",
  padding: "0 11px",
  color: theme.colors.textPrimary,
};

const selectStyle: React.CSSProperties = {
  ...inputStyle,
  cursor: "pointer",
};

const datePlaceholderStyle: React.CSSProperties = {
  minHeight: "38px",
  display: "flex",
  alignItems: "center",
  padding: "0 11px",
  borderRadius: "10px",
  border: `1px dashed ${theme.colors.border}`,
  background: "rgba(248, 250, 252, 0.72)",
  color: theme.colors.textSecondary,
  fontSize: "12px",
};

const tableMetaStyle: React.CSSProperties = {
  display: "grid",
  gap: "2px",
  justifyItems: "end",
  color: theme.colors.textSecondary,
  fontSize: "12px",
  whiteSpace: "nowrap",
};

const emptyWrapStyle: React.CSSProperties = {
  padding: "16px",
};

const tableWrapperStyle: React.CSSProperties = {
  maxHeight: "min(58vh, 620px)",
  overflow: "auto",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "separate",
  borderSpacing: 0,
  minWidth: "980px",
};

const thStyle: React.CSSProperties = {
  position: "sticky",
  top: 0,
  zIndex: 1,
  padding: "11px 12px",
  fontSize: "12px",
  fontWeight: 800,
  textAlign: "start",
  background: "rgba(248, 250, 252, 0.96)",
  borderBottom: `1px solid ${theme.colors.border}`,
};

const tdStyle: React.CSSProperties = {
  padding: "11px 12px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "13px",
  verticalAlign: "middle",
};

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
  fontWeight: 800,
};

const countBadgeStyle: React.CSSProperties = {
  background: "#e0f2fe",
  padding: "4px 9px",
  borderRadius: "999px",
  fontWeight: 700,
  fontSize: "12px",
};

const actionsStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "6px",
  flexWrap: "wrap",
};

const actionLinkStyle: React.CSSProperties = {
  minHeight: "30px",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "0 10px",
  borderRadius: "9px",
  border: `1px solid ${theme.colors.border}`,
  background: "#ffffff",
  color: theme.colors.primaryDark,
  textDecoration: "none",
  fontSize: "12px",
  fontWeight: 700,
};

const actionButtonStyle: React.CSSProperties = {
  ...actionLinkStyle,
  color: "#ffffff",
  background: theme.colors.primary,
  border: `1px solid ${theme.colors.primary}`,
};

const tableFooterStyle: React.CSSProperties = {
  padding: "10px 16px",
  color: theme.colors.textSecondary,
  fontSize: "12px",
  borderTop: `1px solid ${theme.colors.border}`,
  background: "rgba(248, 250, 252, 0.66)",
};

export default PurchaseInvoicesPage;
