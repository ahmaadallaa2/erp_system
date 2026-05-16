import { useEffect, useState } from "react";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
  StatusBadge,
  toBusinessLabel,
} from "../../../components/ui/mvp";
import { theme } from "../../../styles/theme";
import { listProducts } from "../../products/api/list-products";
import type { Product } from "../../products/types/product";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { listStockTransactions } from "../api/list-stock-transactions";
import type { StockTransaction } from "../types/stock-transaction";

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
        setError("Failed to load stock transactions.");
      } finally {
        setLoading(false);
      }
    }

    loadTransactions();
  }, []);

  return (
    <main>
      <PageHeader title="Stock Transactions" subtitle="Inventory transaction documents." />

      {loading && <LoadingState label="Loading stock transactions..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && transactions.length === 0 && (
        <EmptyState
          title="No stock transactions found"
          message="Inventory documents will appear here once created."
        />
      )}

      {!loading && !error && transactions.length > 0 && (
        <div style={tableCardStyle}>
          <table style={tableStyle}>
            <thead style={tableHeadStyle}>
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
    return (
      warehousesMap[transaction.destination_warehouse] ||
      transaction.destination_warehouse
    );
  }

  return "-";
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

export default StockTransactionsPage;
