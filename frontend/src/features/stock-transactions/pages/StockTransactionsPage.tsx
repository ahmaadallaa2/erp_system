import { useEffect, useMemo, useState } from "react";
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
  toBusinessLabel,
} from "../../../components/ui/mvp";
import { getApiErrorMessage } from "../../../lib/api/errors";
import { theme } from "../../../styles/theme";
import { listProducts } from "../../products/api/list-products";
import type { Product } from "../../products/types/product";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { listStockTransactions } from "../api/list-stock-transactions";
import type { StockTransaction } from "../types/stock-transaction";

const searchStorageKey = "erp.stock-transactions.search";

function StockTransactionsPage() {
  const [transactions, setTransactions] = useState<StockTransaction[]>([]);
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [draftQuery, setDraftQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    async function loadTransactions() {
      try {
        setLoading(true);
        setError("");

        const [transactionsData, warehousesData, productsData] = await Promise.all([
          listStockTransactions(),
          listWarehouses(),
          listProducts(),
        ]);

        setTransactions(Array.isArray(transactionsData) ? transactionsData : []);

        const nextWarehousesMap: Record<string, string> = {};
        (Array.isArray(warehousesData) ? warehousesData : []).forEach(
          (warehouse: Warehouse) => {
            nextWarehousesMap[warehouse.id] = warehouse.name;
          }
        );
        setWarehousesMap(nextWarehousesMap);

        const nextProductsMap: Record<string, string> = {};
        (Array.isArray(productsData) ? productsData : []).forEach((product: Product) => {
          nextProductsMap[product.id] = product.name;
        });
        setProductsMap(nextProductsMap);
      } catch (err) {
        console.error("Stock Transactions error:", err);
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    loadTransactions();
  }, []);

  const typeOptions = useMemo(
    () => Array.from(new Set(transactions.map((transaction) => transaction.transaction_type))).filter(Boolean),
    [transactions]
  );

  const statusOptions = useMemo(
    () => Array.from(new Set(transactions.map((transaction) => transaction.status))).filter(Boolean),
    [transactions]
  );

  const filteredTransactions = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return transactions.filter((transaction) => {
      const matchesQuery =
        !normalizedQuery ||
        transaction.code.toLowerCase().includes(normalizedQuery) ||
        (transaction.reference || "").toLowerCase().includes(normalizedQuery);
      const matchesType = typeFilter === "all" || transaction.transaction_type === typeFilter;
      const matchesStatus = statusFilter === "all" || transaction.status === statusFilter;

      return matchesQuery && matchesType && matchesStatus;
    });
  }, [transactions, query, typeFilter, statusFilter]);

  const draftCount = filteredTransactions.filter((transaction) => transaction.status === "draft").length;
  const postedCount = filteredTransactions.filter((transaction) => transaction.status === "posted").length;
  const itemCount = filteredTransactions.reduce((total, transaction) => total + transaction.items.length, 0);

  function applySearch() {
    const nextQuery = draftQuery.trim();
    setQuery(nextQuery);
    sessionStorage.setItem(searchStorageKey, nextQuery);
  }

  function clearFilters() {
    setDraftQuery("");
    setQuery("");
    setTypeFilter("all");
    setStatusFilter("all");
    sessionStorage.removeItem(searchStorageKey);
  }

  return (
    <main style={pageStyle}>
      <PageHeader title="Stock Transactions" subtitle="Inventory transaction documents." />

      {loading && <LoadingState label="Loading stock transactions..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && (
        <div style={workspaceStyle}>
          <section style={summaryGridStyle}>
            <MetricCard title="Total Transactions" value={formatNumber(filteredTransactions.length)} tone="info" />
            <MetricCard title="Draft Transactions" value={formatNumber(draftCount)} tone="warning" />
            <MetricCard title="Posted Transactions" value={formatNumber(postedCount)} tone="success" />
            <MetricCard title="Transaction Lines" value={formatNumber(itemCount)} tone="neutral" />
          </section>

          <section style={tableCardStyle}>
            <div style={filtersBarStyle}>
              <SearchField
                id="transaction-search"
                value={draftQuery}
                onChange={setDraftQuery}
                onSearch={applySearch}
                onClear={clearFilters}
                placeholder="Reference or code"
              />

              <div style={filterGroupStyle}>
                <label style={filterLabelStyle} htmlFor="transaction-type">
                  Type
                </label>
                <select
                  id="transaction-type"
                  value={typeFilter}
                  onChange={(event) => setTypeFilter(event.target.value)}
                  style={inputStyle}
                >
                  <option value="all">All</option>
                  {typeOptions.map((type) => (
                    <option key={type} value={type}>
                      {toBusinessLabel(type)}
                    </option>
                  ))}
                </select>
              </div>

              <div style={filterGroupStyle}>
                <label style={filterLabelStyle} htmlFor="transaction-status">
                  Status
                </label>
                <select
                  id="transaction-status"
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                  style={inputStyle}
                >
                  <option value="all">All</option>
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {toBusinessLabel(status)}
                    </option>
                  ))}
                </select>
              </div>

              <div style={tableMetaStyle}>
                <strong>{filteredTransactions.length}</strong>
                <span>of {transactions.length} transactions</span>
              </div>

              <ClearFiltersButton onClick={clearFilters} />
            </div>

            {filteredTransactions.length === 0 ? (
              <div style={emptyWrapStyle}>
                <EmptyState title="No stock transactions found" message="Adjust filters or create inventory documents from the backend workflow." />
              </div>
            ) : (
              <div style={tableWrapperStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Code</th>
                      <th style={thStyle}>Type</th>
                      <th style={thStyle}>Warehouse</th>
                      <th style={thStyle}>Date</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>Reference</th>
                      <th style={thStyle}>Items</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTransactions.map((transaction) => (
                      <tr key={transaction.id}>
                        <td style={tdStrongStyle}>{transaction.code}</td>
                        <td style={tdStyle}>{toBusinessLabel(transaction.transaction_type)}</td>
                        <td style={tdStyle}>{getWarehouseLabel(transaction, warehousesMap)}</td>
                        <td style={tdStyle}>{transaction.date}</td>
                        <td style={tdStyle}>
                          <StatusBadge status={transaction.status} />
                        </td>
                        <td style={tdStyle}>{transaction.reference || "-"}</td>
                        <td style={tdStyle}>
                          {transaction.items.length === 0
                            ? "0"
                            : transaction.items
                                .map((item) => productsMap[item.product] || item.product)
                                .join(", ")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

function getWarehouseLabel(
  transaction: StockTransaction,
  warehousesMap: Record<string, string>
) {
  if (transaction.source_warehouse) {
    return warehousesMap[transaction.source_warehouse] || transaction.source_warehouse;
  }

  if (transaction.destination_warehouse) {
    return warehousesMap[transaction.destination_warehouse] || transaction.destination_warehouse;
  }

  return "-";
}

const pageStyle: React.CSSProperties = { background: "transparent", minWidth: 0 };
const workspaceStyle: React.CSSProperties = { display: "grid", gap: "16px" };
const summaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: "14px",
};
const tableCardStyle: React.CSSProperties = {
  background: "linear-gradient(145deg, rgba(255,255,255,0.94), rgba(236,254,255,0.38))",
  border: "1px solid rgba(255, 255, 255, 0.78)",
  borderRadius: "20px",
  overflow: "hidden",
  boxShadow: "0 18px 42px rgba(15, 23, 42, 0.07), inset 0 1px 0 rgba(255,255,255,0.86)",
  backdropFilter: "blur(22px) saturate(145%)",
};
const filtersBarStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(220px, 1fr) minmax(150px, 0.48fr) minmax(150px, 0.48fr) auto auto",
  gap: "12px",
  alignItems: "end",
  padding: "14px 16px",
  borderBottom: `1px solid ${theme.colors.border}`,
};
const filterGroupStyle: React.CSSProperties = { display: "grid", gap: "6px", minWidth: 0 };
const filterLabelStyle: React.CSSProperties = { color: theme.colors.textSecondary, fontSize: "12px", fontWeight: 700 };
const inputStyle: React.CSSProperties = {
  height: "38px",
  borderRadius: "10px",
  border: `1px solid ${theme.colors.border}`,
  background: "#ffffff",
  padding: "0 11px",
  color: theme.colors.textPrimary,
  fontSize: "13px",
};
const tableMetaStyle: React.CSSProperties = {
  display: "grid",
  gap: "2px",
  justifyItems: "end",
  color: theme.colors.textSecondary,
  fontSize: "12px",
  whiteSpace: "nowrap",
};
const emptyWrapStyle: React.CSSProperties = { padding: "16px" };
const tableWrapperStyle: React.CSSProperties = { maxHeight: "min(58vh, 620px)", overflow: "auto" };
const tableStyle: React.CSSProperties = { width: "100%", borderCollapse: "separate", borderSpacing: 0, minWidth: "980px" };
const thStyle: React.CSSProperties = {
  position: "sticky",
  top: 0,
  zIndex: 1,
  textAlign: "start",
  padding: "11px 12px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "12px",
  fontWeight: 800,
  color: theme.colors.textSecondary,
  background: "rgba(248, 250, 252, 0.96)",
  whiteSpace: "nowrap",
};
const tdStyle: React.CSSProperties = {
  padding: "11px 12px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "13px",
  color: theme.colors.textPrimary,
};
const tdStrongStyle: React.CSSProperties = { ...tdStyle, fontWeight: 800 };

export default StockTransactionsPage;
