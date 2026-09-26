import { useEffect, useMemo, useState } from "react";
import {
  EmptyState,
  ErrorMessage,
  ClearFiltersButton,
  LoadingState,
  MetricCard,
  PageHeader,
  SearchField,
  formatNumber,
} from "../../../components/ui/mvp";
import { getApiErrorMessage } from "../../../lib/api/errors";
import { theme } from "../../../styles/theme";
import { listProducts } from "../../products/api/list-products";
import type { Product } from "../../products/types/product";
import { listStockTransactions } from "../../stock-transactions/api/list-stock-transactions";
import type { StockTransaction } from "../../stock-transactions/types/stock-transaction";
import { listStockMovements } from "../api/list-stock-movements";
import type { StockMovement } from "../types/stock-movement";

type TransactionLabel = {
  code: string;
  reference: string | null;
};

const searchStorageKey = "erp.stock-movements.search";

function StockMovementsPage() {
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [transactionsMap, setTransactionsMap] = useState<Record<string, TransactionLabel>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [draftQuery, setDraftQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");

  useEffect(() => {
    async function loadMovements() {
      try {
        setLoading(true);
        setError("");

        const [movementsData, productsData, transactionsData] = await Promise.all([
          listStockMovements(),
          listProducts(),
          listStockTransactions(),
        ]);

        setMovements(Array.isArray(movementsData) ? movementsData : []);

        const nextProductsMap: Record<string, string> = {};
        (Array.isArray(productsData) ? productsData : []).forEach((product: Product) => {
          nextProductsMap[product.id] = product.name;
        });
        setProductsMap(nextProductsMap);

        const nextTransactionsMap: Record<string, TransactionLabel> = {};
        (Array.isArray(transactionsData) ? transactionsData : []).forEach(
          (transaction: StockTransaction) => {
            nextTransactionsMap[transaction.id] = {
              code: transaction.code,
              reference: transaction.reference,
            };
          }
        );
        setTransactionsMap(nextTransactionsMap);
      } catch (err) {
        console.error("Stock movements error:", err);
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    loadMovements();
  }, []);

  const filteredMovements = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return movements.filter((movement) => {
      const productLabel = productsMap[movement.product] || movement.product;
      const transactionLabel = transactionsMap[movement.transaction];
      const transactionCode = transactionLabel?.code || movement.transaction;
      const transactionReference = transactionLabel?.reference || "";

      return (
        !normalizedQuery ||
        productLabel.toLowerCase().includes(normalizedQuery) ||
        transactionCode.toLowerCase().includes(normalizedQuery) ||
        transactionReference.toLowerCase().includes(normalizedQuery)
      );
    });
  }, [movements, productsMap, transactionsMap, query]);

  const totalQuantity = filteredMovements.reduce(
    (total, movement) => total + Number(movement.quantity || 0),
    0
  );
  const linkedTransactionsCount = new Set(filteredMovements.map((movement) => movement.transaction)).size;

  function applySearch() {
    const nextQuery = draftQuery.trim();
    setQuery(nextQuery);
    sessionStorage.setItem(searchStorageKey, nextQuery);
  }

  function clearFilters() {
    setDraftQuery("");
    setQuery("");
    sessionStorage.removeItem(searchStorageKey);
  }

  return (
    <main style={pageStyle}>
      <PageHeader title="Stock Movements" subtitle="Item-level inventory movement lines." />

      {loading && <LoadingState label="Loading stock movements..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && (
        <div style={workspaceStyle}>
          <section style={summaryGridStyle}>
            <MetricCard title="Movement Lines" value={formatNumber(filteredMovements.length)} tone="info" />
            <MetricCard title="Total Quantity" value={formatNumber(totalQuantity)} tone="neutral" />
            <MetricCard title="Linked Transactions" value={formatNumber(linkedTransactionsCount)} tone="success" />
          </section>

          <section style={tableCardStyle}>
            <div style={filtersBarStyle}>
              <SearchField
                id="movement-search"
                value={draftQuery}
                onChange={setDraftQuery}
                onSearch={applySearch}
                onClear={clearFilters}
                placeholder="Product, transaction, or reference"
              />

              <div style={tableMetaStyle}>
                <strong>{filteredMovements.length}</strong>
                <span>of {movements.length} movements</span>
              </div>

              <ClearFiltersButton onClick={clearFilters} />
            </div>

            {filteredMovements.length === 0 ? (
              <div style={emptyWrapStyle}>
                <EmptyState title="No stock movements found" message="Adjust filters or wait for posted stock transactions." />
              </div>
            ) : (
              <div style={tableWrapperStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Transaction</th>
                      <th style={thStyle}>Reference</th>
                      <th style={thStyle}>Product</th>
                      <th style={rightThStyle}>Quantity</th>
                      <th style={rightThStyle}>Unit Cost</th>
                      <th style={thStyle}>Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredMovements.map((movement) => {
                      const transactionLabel = transactionsMap[movement.transaction];

                      return (
                        <tr key={movement.id}>
                          <td style={tdStrongStyle}>
                            {transactionLabel?.code || movement.transaction}
                          </td>
                          <td style={tdStyle}>{transactionLabel?.reference || "-"}</td>
                          <td style={tdStyle}>{productsMap[movement.product] || movement.product}</td>
                          <td style={rightTdStyle}>{movement.quantity}</td>
                          <td style={rightTdStyle}>{movement.unit_cost}</td>
                          <td style={tdStyle}>{movement.note || "-"}</td>
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
  gridTemplateColumns: "minmax(240px, 1fr) auto auto",
  gap: "12px",
  alignItems: "end",
  padding: "14px 16px",
  borderBottom: `1px solid ${theme.colors.border}`,
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
const tdStrongStyle: React.CSSProperties = { ...tdStyle, fontWeight: 800 };
const rightTdStyle: React.CSSProperties = { ...tdStyle, textAlign: "end", fontVariantNumeric: "tabular-nums" };

export default StockMovementsPage;
