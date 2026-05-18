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
import { listProducts } from "../api/list-products";
import type { Product } from "../types/product";

const searchStorageKey = "erp.products.search";

function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [draftQuery, setDraftQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    async function loadProducts() {
      try {
        setLoading(true);
        setError("");
        const result = await listProducts();
        setProducts(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error("Products load error:", err);
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    loadProducts();
  }, []);

  const productTypes = useMemo(
    () => Array.from(new Set(products.map((product) => product.product_type))).filter(Boolean),
    [products]
  );

  const filteredProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return products.filter((product) => {
      const matchesQuery =
        !normalizedQuery ||
        product.name.toLowerCase().includes(normalizedQuery) ||
        product.sku.toLowerCase().includes(normalizedQuery);
      const matchesType = typeFilter === "all" || product.product_type === typeFilter;

      return matchesQuery && matchesType;
    });
  }, [products, query, typeFilter]);

  const activeCount = filteredProducts.filter((product) => product.is_active).length;
  const serviceCount = filteredProducts.filter((product) => product.product_type === "service").length;
  const stockCount = filteredProducts.length - serviceCount;

  function applySearch() {
    const nextQuery = draftQuery.trim();
    setQuery(nextQuery);
    sessionStorage.setItem(searchStorageKey, nextQuery);
  }

  function clearFilters() {
    setDraftQuery("");
    setQuery("");
    setTypeFilter("all");
    sessionStorage.removeItem(searchStorageKey);
  }

  return (
    <main style={pageStyle}>
      <PageHeader title="Products" subtitle="Inventory and service items used by purchase and sales invoices." />

      {loading && <LoadingState label="Loading products..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && (
        <div style={workspaceStyle}>
          <section style={summaryGridStyle}>
            <MetricCard title="Total Products" value={formatNumber(filteredProducts.length)} tone="info" />
            <MetricCard title="Active Items" value={formatNumber(activeCount)} tone="success" />
            <MetricCard title="Stock Items" value={formatNumber(stockCount)} tone="neutral" />
            <MetricCard title="Service Items" value={formatNumber(serviceCount)} tone="warning" />
          </section>

          <section style={tableCardStyle}>
            <div style={filtersBarStyle}>
              <SearchField
                id="product-search"
                value={draftQuery}
                onChange={setDraftQuery}
                onSearch={applySearch}
                onClear={clearFilters}
                placeholder="Product name or code"
              />

              <div style={filterGroupStyle}>
                <label style={filterLabelStyle} htmlFor="product-type">
                  Product Type
                </label>
                <select
                  id="product-type"
                  value={typeFilter}
                  onChange={(event) => setTypeFilter(event.target.value)}
                  style={inputStyle}
                >
                  <option value="all">All</option>
                  {productTypes.map((type) => (
                    <option key={type} value={type}>
                      {toBusinessLabel(type)}
                    </option>
                  ))}
                </select>
              </div>

              <div style={tableMetaStyle}>
                <strong>{filteredProducts.length}</strong>
                <span>of {products.length} products</span>
              </div>

              <ClearFiltersButton onClick={clearFilters} />
            </div>

            {filteredProducts.length === 0 ? (
              <div style={emptyWrapStyle}>
                <EmptyState title="No products found" message="Adjust filters or add products from the backend workflow." />
              </div>
            ) : (
              <div style={tableWrapperStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>SKU</th>
                      <th style={thStyle}>Product Name</th>
                      <th style={thStyle}>Type</th>
                      <th style={{ ...thStyle, textAlign: "end" }}>Cost Price</th>
                      <th style={{ ...thStyle, textAlign: "end" }}>Sale Price</th>
                      <th style={{ ...thStyle, textAlign: "end" }}>Reorder Point</th>
                      <th style={thStyle}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredProducts.map((product) => (
                      <tr key={product.id}>
                        <td style={tdStrongStyle}>{product.sku}</td>
                        <td style={tdStyle}>{product.name}</td>
                        <td style={tdStyle}>{toBusinessLabel(product.product_type)}</td>
                        <td style={rightTdStyle}>{product.cost_price}</td>
                        <td style={rightTdStyle}>{product.sale_price}</td>
                        <td style={rightTdStyle}>{product.reorder_point}</td>
                        <td style={tdStyle}>
                          <StatusBadge status={product.is_active ? "active" : "inactive"} />
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
  gridTemplateColumns: "minmax(240px, 1fr) minmax(180px, 0.6fr) auto auto",
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
const tableStyle: React.CSSProperties = { width: "100%", borderCollapse: "separate", borderSpacing: 0, minWidth: "860px" };
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
const rightTdStyle: React.CSSProperties = { ...tdStyle, textAlign: "end", fontVariantNumeric: "tabular-nums" };

export default ProductsPage;
