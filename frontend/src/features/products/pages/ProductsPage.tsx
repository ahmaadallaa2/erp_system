import { useEffect, useState } from "react";
import { listProducts } from "../api/list-products";
import type { Product } from "../types/product";

function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadProducts() {
      try {
        setLoading(true);
        setError("");

        const result = await listProducts();
        setProducts(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error("Products load error:", err);
        setError("Failed to load products.");
      } finally {
        setLoading(false);
      }
    }

    loadProducts();
  }, []);

  return (
    <main>
      <div style={{ marginBottom: "20px" }}>
        <h1 style={{ margin: 0 }}>Products</h1>
        <p style={{ marginTop: "8px", color: "#666" }}>
          Manage inventory products.
        </p>
      </div>

      {loading && <p>Loading products...</p>}

      {!loading && error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && !error && products.length === 0 && <p>No products found.</p>}

      {!loading && !error && products.length > 0 && (
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
                <th style={thStyle}>SKU</th>
                <th style={thStyle}>Name</th>
                <th style={thStyle}>Type</th>
                <th style={thStyle}>Cost Price</th>
                <th style={thStyle}>Sale Price</th>
                <th style={thStyle}>Reorder Point</th>
                <th style={thStyle}>Status</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id}>
                  <td style={tdStyle}>{product.sku}</td>
                  <td style={tdStyle}>{product.name}</td>
                  <td style={tdStyle}>{product.product_type}</td>
                  <td style={tdStyle}>{product.cost_price}</td>
                  <td style={tdStyle}>{product.sale_price}</td>
                  <td style={tdStyle}>{product.reorder_point}</td>
                  <td style={tdStyle}>
                    {product.is_active ? "Active" : "Inactive"}
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

export default ProductsPage;