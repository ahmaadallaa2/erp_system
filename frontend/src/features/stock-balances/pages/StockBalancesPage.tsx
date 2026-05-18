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
} from "../../../components/ui/mvp";
import { getApiErrorMessage } from "../../../lib/api/errors";
import { theme } from "../../../styles/theme";
import { listProducts } from "../../products/api/list-products";
import type { Product } from "../../products/types/product";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { listStockBalances } from "../api/list-stock-balances";
import type { StockBalance } from "../types/stock-balance";

const searchStorageKey = "erp.stock-balances.search";

function StockBalancesPage() {
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [draftQuery, setDraftQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [stockFilter, setStockFilter] = useState("all");

  useEffect(() => {
    async function loadBalances() {
      try {
        setLoading(true);
        setError("");

        const [balancesData, productsData, warehousesData] = await Promise.all([
          listStockBalances(),
          listProducts(),
          listWarehouses(),
        ]);

        setBalances(Array.isArray(balancesData) ? balancesData : []);

        const nextProductsMap: Record<string, string> = {};
        (Array.isArray(productsData) ? productsData : []).forEach((product: Product) => {
          nextProductsMap[product.id] = product.name;
        });
        setProductsMap(nextProductsMap);

        const nextWarehousesMap: Record<string, string> = {};
        (Array.isArray(warehousesData) ? warehousesData : []).forEach(
          (warehouse: Warehouse) => {
            nextWarehousesMap[warehouse.id] = warehouse.name;
          }
        );
        setWarehousesMap(nextWarehousesMap);
      } catch (err) {
        console.error("Stock balances error:", err);
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    loadBalances();
  }, []);

  const filteredBalances = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return balances.filter((balance) => {
      const productLabel = productsMap[balance.product] || balance.product;
      const isLowStock = isLowStockBalance(balance);
      const matchesQuery =
        !normalizedQuery || productLabel.toLowerCase().includes(normalizedQuery);
      const matchesStockFilter = stockFilter === "all" || (stockFilter === "low" && isLowStock);

      return matchesQuery && matchesStockFilter;
    });
  }, [balances, productsMap, query, stockFilter]);

  const totalQuantity = filteredBalances.reduce(
    (total, balance) => total + Number(balance.quantity || 0),
    0
  );
  const totalAvailable = filteredBalances.reduce(
    (total, balance) => total + Number(balance.available_quantity || 0),
    0
  );
  const lowStockCount = filteredBalances.filter(isLowStockBalance).length;

  function applySearch() {
    const nextQuery = draftQuery.trim();
    setQuery(nextQuery);
    sessionStorage.setItem(searchStorageKey, nextQuery);
  }

  function clearFilters() {
    setDraftQuery("");
    setQuery("");
    setStockFilter("all");
    sessionStorage.removeItem(searchStorageKey);
  }

  return (
    <main style={pageStyle}>
      <PageHeader title="Stock Balances" subtitle="Current stock by product and warehouse." />

      {loading && <LoadingState label="Loading stock balances..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && (
        <div style={workspaceStyle}>
          <section style={summaryGridStyle}>
            <MetricCard title="Balance Rows" value={formatNumber(filteredBalances.length)} tone="info" />
            <MetricCard title="Total Quantity" value={formatNumber(totalQuantity)} tone="neutral" />
            <MetricCard title="Available Quantity" value={formatNumber(totalAvailable)} tone="success" />
            <MetricCard
              title="Low Stock Rows"
              value={formatNumber(lowStockCount)}
              tone={lowStockCount > 0 ? "warning" : "success"}
            />
          </section>

          <section style={tableCardStyle}>
            <div style={filtersBarStyle}>
              <SearchField
                id="balance-search"
                value={draftQuery}
                onChange={setDraftQuery}
                onSearch={applySearch}
                onClear={clearFilters}
                placeholder="Product name"
              />

              <div style={filterGroupStyle}>
                <label style={filterLabelStyle} htmlFor="stock-filter">
                  Stock Health
                </label>
                <select
                  id="stock-filter"
                  value={stockFilter}
                  onChange={(event) => setStockFilter(event.target.value)}
                  style={inputStyle}
                >
                  <option value="all">All</option>
                  <option value="low">Low Stock</option>
                </select>
              </div>

              <div style={tableMetaStyle}>
                <strong>{filteredBalances.length}</strong>
                <span>of {balances.length} balances</span>
              </div>

              <ClearFiltersButton onClick={clearFilters} />
            </div>

            {filteredBalances.length === 0 ? (
              <div style={emptyWrapStyle}>
                <EmptyState title="No stock balances found" message="Adjust filters or wait for posted stock activity." />
              </div>
            ) : (
              <div style={tableWrapperStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Product</th>
                      <th style={thStyle}>Warehouse</th>
                      <th style={rightThStyle}>Quantity</th>
                      <th style={rightThStyle}>Reserved</th>
                      <th style={rightThStyle}>Available</th>
                      <th style={rightThStyle}>Reorder Point</th>
                      <th style={thStyle}>Stock Health</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBalances.map((balance) => {
                      const lowStock = isLowStockBalance(balance);

                      return (
                        <tr key={balance.id} style={lowStock ? lowStockRowStyle : undefined}>
                          <td style={tdStyle}>{productsMap[balance.product] || balance.product}</td>
                          <td style={tdStyle}>
                            {warehousesMap[balance.warehouse] || balance.warehouse}
                          </td>
                          <td style={rightTdStyle}>{balance.quantity}</td>
                          <td style={rightTdStyle}>{balance.reserved_quantity}</td>
                          <td style={rightTdStyle}>{balance.available_quantity}</td>
                          <td style={rightTdStyle}>{balance.reorder_point}</td>
                          <td style={tdStyle}>
                            <StatusBadge
                              status={lowStock ? "Low Stock" : "Available"}
                              tone={lowStock ? "warning" : "success"}
                            />
                          </td>
                        </tr>
                      );
                    })}
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

function isLowStockBalance(balance: StockBalance) {
  return Number(balance.available_quantity) <= Number(balance.reorder_point);
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
  gridTemplateColumns: "minmax(240px, 1fr) minmax(160px, 0.5fr) auto auto",
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
const tableStyle: React.CSSProperties = { width: "100%", borderCollapse: "separate", borderSpacing: 0, minWidth: "900px" };
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
const rightThStyle: React.CSSProperties = { ...thStyle, textAlign: "end" };
const tdStyle: React.CSSProperties = {
  padding: "11px 12px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "13px",
  color: theme.colors.textPrimary,
};
const rightTdStyle: React.CSSProperties = { ...tdStyle, textAlign: "end", fontVariantNumeric: "tabular-nums" };
const lowStockRowStyle: React.CSSProperties = { background: "rgba(245, 158, 11, 0.06)" };

export default StockBalancesPage;
