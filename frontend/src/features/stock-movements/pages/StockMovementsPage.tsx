import { useEffect, useState } from "react";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
} from "../../../components/ui/mvp";
import { theme } from "../../../styles/theme";
import { listProducts } from "../../products/api/list-products";
import type { Product } from "../../products/types/product";
import { listStockTransactions } from "../../stock-transactions/api/list-stock-transactions";
import type { StockTransaction } from "../../stock-transactions/types/stock-transaction";
import { listStockMovements } from "../api/list-stock-movements";
import type { StockMovement } from "../types/stock-movement";

function StockMovementsPage() {
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [transactionsMap, setTransactionsMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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

        const nextTransactionsMap: Record<string, string> = {};
        (Array.isArray(transactionsData) ? transactionsData : []).forEach(
          (transaction: StockTransaction) => {
            nextTransactionsMap[transaction.id] = transaction.code;
          }
        );
        setTransactionsMap(nextTransactionsMap);
      } catch (err) {
        console.error("Stock movements error:", err);
        setError("Failed to load stock movements.");
      } finally {
        setLoading(false);
      }
    }

    loadMovements();
  }, []);

  return (
    <main>
      <PageHeader title="Stock Movements" subtitle="Item-level inventory movement lines." />

      {loading && <LoadingState label="Loading stock movements..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && movements.length === 0 && (
        <EmptyState
          title="No stock movements found"
          message="Movement lines appear after stock transactions are posted."
        />
      )}

      {!loading && !error && movements.length > 0 && (
        <div style={tableCardStyle}>
          <table style={tableStyle}>
            <thead style={tableHeadStyle}>
              <tr>
                <th style={thStyle}>Transaction</th>
                <th style={thStyle}>Product</th>
                <th style={rightThStyle}>Quantity</th>
                <th style={rightThStyle}>Unit Cost</th>
                <th style={thStyle}>Note</th>
              </tr>
            </thead>
            <tbody>
              {movements.map((movement) => (
                <tr key={movement.id}>
                  <td style={tdStrongStyle}>
                    {transactionsMap[movement.transaction] || movement.transaction}
                  </td>
                  <td style={tdStyle}>{productsMap[movement.product] || movement.product}</td>
                  <td style={rightTdStyle}>{movement.quantity}</td>
                  <td style={rightTdStyle}>{movement.unit_cost}</td>
                  <td style={tdStyle}>{movement.note || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

const tableCardStyle: React.CSSProperties = {
  overflowX: "auto",
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "8px",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
};

const tableHeadStyle: React.CSSProperties = {
  background: "#f8fafc",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "12px 14px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "13px",
  color: theme.colors.textSecondary,
};

const rightThStyle: React.CSSProperties = {
  ...thStyle,
  textAlign: "right",
};

const tdStyle: React.CSSProperties = {
  padding: "13px 14px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "14px",
  color: theme.colors.textPrimary,
};

const tdStrongStyle: React.CSSProperties = {
  ...tdStyle,
  fontWeight: 800,
};

const rightTdStyle: React.CSSProperties = {
  ...tdStyle,
  textAlign: "right",
  fontVariantNumeric: "tabular-nums",
};

export default StockMovementsPage;
