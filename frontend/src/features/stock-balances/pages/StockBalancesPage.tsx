import { useEffect, useState } from "react";
import { listStockBalances } from "../api/list-stock-balances";
import type { StockBalance } from "../types/stock-balance";
import { listProducts } from "../../products/api/list-products";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Product } from "../../products/types/product";
import type { Warehouse } from "../../warehouses/types/warehouse";

function StockBalancesPage() {
  const [balances, setBalances] = useState<StockBalance[]>([]);
  const [productsMap, setProductsMap] = useState<Record<string, string>>({});
  const [warehousesMap, setWarehousesMap] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
        setError("Failed to load stock balances.");
      } finally {
        setLoading(false);
      }
    }

    loadBalances();
  }, []);

  return (
    <main>
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>Stock Balances</h1>
        <p style={{ marginTop: "8px", color: "#666" }}>
          View current stock balances by product and warehouse.
        </p>
      </div>

      {loading && <p>Loading stock balances...</p>}

      {!loading && error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && !error && balances.length === 0 && (
        <p>No stock balances found.</p>
      )}

      {!loading && !error && balances.length > 0 && (
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
                <th style={thStyle}>Product</th>
                <th style={thStyle}>Warehouse</th>
                <th style={thStyle}>Quantity</th>
                <th style={thStyle}>Reserved</th>
                <th style={thStyle}>Available</th>
                <th style={thStyle}>Reorder Point</th>
              </tr>
            </thead>
            <tbody>
              {balances.map((balance) => (
                <tr key={balance.id}>
                  <td style={tdStyle}>
                    {productsMap[balance.product] || balance.product}
                  </td>
                  <td style={tdStyle}>
                    {warehousesMap[balance.warehouse] || balance.warehouse}
                  </td>
                  <td style={tdStyle}>{balance.quantity}</td>
                  <td style={tdStyle}>{balance.reserved_quantity}</td>
                  <td style={tdStyle}>{balance.available_quantity}</td>
                  <td style={tdStyle}>{balance.reorder_point}</td>
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

export default StockBalancesPage;