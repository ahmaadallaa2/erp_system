import { useEffect, useState } from "react";
import { listStockTransactions } from "../api/list-stock-transactions";
import type { StockTransaction } from "../types/stock-transaction";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import { listProducts } from "../../products/api/list-products";
import type { Warehouse } from "../../warehouses/types/warehouse";
import type { Product } from "../../products/types/product";

function StockTransactionsPage() {
  const [transactions, setTransactions] = useState<StockTransaction[]>([]);
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
        setError("Failed to load transactions.");
      } finally {
        setLoading(false);
      }
    }

    loadTransactions();
  }, []);

  return (
    <main>
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>Stock Transactions</h1>
        <p style={{ marginTop: "8px", color: "#666" }}>
          Manage stock transaction documents.
        </p>
      </div>

      {loading && <p>Loading stock transactions...</p>}

      {!loading && error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && !error && transactions.length === 0 && (
        <p>No stock transactions found.</p>
      )}

      {!loading && !error && transactions.length > 0 && (
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
              {transactions.map((transaction) => (
                <tr key={transaction.id}>
                  <td style={tdStyle}>{transaction.code}</td>
                  <td style={tdStyle}>{transaction.transaction_type}</td>
                  <td style={tdStyle}>
                    {transaction.source_warehouse
                      ? warehousesMap[transaction.source_warehouse] ||
                        transaction.source_warehouse
                      : transaction.destination_warehouse
                        ? warehousesMap[transaction.destination_warehouse] ||
                          transaction.destination_warehouse
                        : "-"}
                  </td>
                  <td style={tdStyle}>{transaction.date}</td>
                  <td style={tdStyle}>{transaction.status}</td>
                  <td style={tdStyle}>{transaction.reference || "-"}</td>
                  <td style={tdStyle}>
                    {transaction.items.length === 0
                      ? "0"
                      : transaction.items
                          .map((item) => productsMap[item.product] || item.product)
                          .join(" , ")}
                  </td>
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

export default StockTransactionsPage;