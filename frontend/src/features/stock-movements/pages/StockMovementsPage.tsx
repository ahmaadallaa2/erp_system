import { useEffect, useState } from "react";
import { listStockMovements } from "../api/list-stock-movements";
import type { StockMovement } from "../types/stock-movement";
import { listProducts } from "../../products/api/list-products";
import { listStockTransactions } from "../../stock-transactions/api/list-stock-transactions";
import type { Product } from "../../products/types/product";
import type { StockTransaction } from "../../stock-transactions/types/stock-transaction";

function StockMovementsPage() {
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [transactionsMap, setTransactionsMap] = useState<Record<string, string>>(
    {}
  );
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
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>Stock Movements</h1>
        <p style={{ marginTop: "8px", color: "#666" }}>
          View item-level stock movement lines.
        </p>
      </div>

      {loading && <p>Loading stock movements...</p>}

      {!loading && error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && !error && movements.length === 0 && (
        <p>No stock movements found.</p>
      )}

      {!loading && !error && movements.length > 0 && (
        <div
          style={{
            overflowX: "auto",
            background: "#fff",
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
                <th style={thStyle}>Transaction</th>
                <th style={thStyle}>Product</th>
                <th style={thStyle}>Quantity</th>
                <th style={thStyle}>Unit Cost</th>
                <th style={thStyle}>Note</th>
              </tr>
            </thead>
            <tbody>
              {movements.map((movement) => (
                <tr key={movement.id}>
                  <td style={tdStyle}>
                    {transactionsMap[movement.transaction] || movement.transaction}
                  </td>
                  <td style={tdStyle}>
                    {productsMap[movement.product] || movement.product}
                  </td>
                  <td style={tdStyle}>{movement.quantity}</td>
                  <td style={tdStyle}>{movement.unit_cost}</td>
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

export default StockMovementsPage;