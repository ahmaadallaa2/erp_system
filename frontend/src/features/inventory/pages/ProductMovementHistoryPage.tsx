import { useEffect, useState } from "react";
import { EmptyState, ErrorMessage, LoadingState, PageHeader, SectionCard } from "../../../components/ui/mvp";
import { getApiErrorMessage } from "../../../lib/api/errors";
import { theme } from "../../../styles/theme";
import { listProducts } from "../../products/api/list-products";
import type { Product } from "../../products/types/product";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { getProductMovementHistory } from "../api/reports-api";
import type { ProductMovementFilters, ProductMovementRow } from "../api/reports-api";

const initialFilters: ProductMovementFilters = {
  product: "",
  warehouse: "",
  start_date: "",
  end_date: "",
  transaction_type: "",
};

function ProductMovementHistoryPage() {
  const [rows, setRows] = useState<ProductMovementRow[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [filters, setFilters] = useState<ProductMovementFilters>(initialFilters);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadReport(nextFilters = filters) {
    try {
      setLoading(true);
      setError("");
      const [reportRows, productsData, warehousesData] = await Promise.all([
        getProductMovementHistory(nextFilters),
        listProducts(),
        listWarehouses(),
      ]);

      setRows(reportRows);
      setProducts(productsData);
      setWarehouses(warehousesData);
    } catch (err) {
      console.error("Product movement report error:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport(initialFilters);
  }, []);

  function updateFilter(key: keyof ProductMovementFilters, value: string) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadReport(filters);
  }

  function clearFilters() {
    setFilters(initialFilters);
    loadReport(initialFilters);
  }

  return (
    <main style={pageStyle}>
      <PageHeader title="تاريخ حركة المنتج" subtitle="تقرير حركات المنتجات حسب المستودع والنوع والفترة." />

      <SectionCard>
        <form onSubmit={handleSubmit} style={filtersStyle}>
          <FilterSelect label="المنتج" value={filters.product || ""} onChange={(value) => updateFilter("product", value)}>
            <option value="">كل المنتجات</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>{product.sku} - {product.name}</option>
            ))}
          </FilterSelect>
          <FilterSelect label="المستودع" value={filters.warehouse || ""} onChange={(value) => updateFilter("warehouse", value)}>
            <option value="">كل المستودعات</option>
            {warehouses.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>{warehouse.code} - {warehouse.name}</option>
            ))}
          </FilterSelect>
          <FilterInput label="من تاريخ" type="date" value={filters.start_date || ""} onChange={(value) => updateFilter("start_date", value)} />
          <FilterInput label="إلى تاريخ" type="date" value={filters.end_date || ""} onChange={(value) => updateFilter("end_date", value)} />
          <FilterSelect label="نوع الحركة" value={filters.transaction_type || ""} onChange={(value) => updateFilter("transaction_type", value)}>
            <option value="">كل الأنواع</option>
            <option value="in">IN</option>
            <option value="out">OUT</option>
            <option value="transfer">TRANSFER</option>
          </FilterSelect>
          <div style={actionsStyle}>
            <button type="submit" style={primaryButtonStyle}>تطبيق</button>
            <button type="button" onClick={clearFilters} style={secondaryButtonStyle}>مسح</button>
          </div>
        </form>
      </SectionCard>

      <ErrorMessage message={error} />
      {loading && <LoadingState label="جاري تحميل تقرير حركة المنتج..." />}

      {!loading && !error && (
        <SectionCard>
          {rows.length === 0 ? (
            <EmptyState title="لا توجد حركات" message="غيّر الفلاتر أو تأكد من وجود حركات مخزون." />
          ) : (
            <div style={tableWrapperStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>التاريخ</th>
                    <th style={thStyle}>المستند</th>
                    <th style={thStyle}>النوع</th>
                    <th style={thStyle}>المنتج</th>
                    <th style={thStyle}>المستودع</th>
                    <th style={rightThStyle}>كمية وارد</th>
                    <th style={rightThStyle}>كمية صادر</th>
                    <th style={rightThStyle}>التكلفة</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={row.id || `${row.date}-${index}`}>
                      <td style={tdStyle}>{row.date}</td>
                      <td style={tdStrongStyle}>{formatValue(row.transaction)}</td>
                      <td style={tdStyle}>{row.transaction_type || row.type || "-"}</td>
                      <td style={tdStyle}>{formatValue(row.product)}</td>
                      <td style={tdStyle}>{formatValue(row.warehouse)}</td>
                      <td style={rightTdStyle}>{row.quantity_in}</td>
                      <td style={rightTdStyle}>{row.quantity_out}</td>
                      <td style={rightTdStyle}>{row.cost}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      )}
    </main>
  );
}

function FilterInput({ label, type, value, onChange }: { label: string; type: string; value: string; onChange: (value: string) => void }) {
  return <label style={fieldStyle}><span style={labelStyle}>{label}</span><input type={type} value={value} onChange={(event) => onChange(event.target.value)} style={inputStyle} /></label>;
}

function FilterSelect({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return <label style={fieldStyle}><span style={labelStyle}>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)} style={inputStyle}>{children}</select></label>;
}

function formatValue(value: unknown) {
  if (!value) return "-";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    return String(record.name || record.code || record.reference || record.id || "-");
  }
  return "-";
}

const pageStyle: React.CSSProperties = { display: "grid", gap: "16px", minWidth: 0 };
const filtersStyle: React.CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr)) auto", gap: "12px", alignItems: "end" };
const fieldStyle: React.CSSProperties = { display: "grid", gap: "6px", minWidth: 0 };
const labelStyle: React.CSSProperties = { color: theme.colors.textSecondary, fontSize: "12px", fontWeight: 800 };
const inputStyle: React.CSSProperties = { height: "38px", borderRadius: "10px", border: `1px solid ${theme.colors.border}`, background: "#fff", padding: "0 11px", color: theme.colors.textPrimary };
const actionsStyle: React.CSSProperties = { display: "flex", gap: "8px", alignItems: "center" };
const primaryButtonStyle: React.CSSProperties = { height: "38px", border: "none", borderRadius: "10px", background: theme.colors.primary, color: "#fff", padding: "0 14px", fontWeight: 800, cursor: "pointer" };
const secondaryButtonStyle: React.CSSProperties = { ...primaryButtonStyle, background: "#fff", color: theme.colors.textSecondary, border: `1px solid ${theme.colors.border}` };
const tableWrapperStyle: React.CSSProperties = { maxHeight: "min(62vh, 680px)", overflow: "auto" };
const tableStyle: React.CSSProperties = { width: "100%", minWidth: "980px", borderCollapse: "separate", borderSpacing: 0 };
const thStyle: React.CSSProperties = { position: "sticky", top: 0, zIndex: 1, textAlign: "start", padding: "11px 12px", borderBottom: `1px solid ${theme.colors.border}`, background: "rgba(248,250,252,.96)", color: theme.colors.textSecondary, fontSize: "12px", fontWeight: 900, whiteSpace: "nowrap" };
const rightThStyle: React.CSSProperties = { ...thStyle, textAlign: "end" };
const tdStyle: React.CSSProperties = { padding: "11px 12px", borderBottom: `1px solid ${theme.colors.border}`, color: theme.colors.textPrimary, fontSize: "13px" };
const tdStrongStyle: React.CSSProperties = { ...tdStyle, fontWeight: 800 };
const rightTdStyle: React.CSSProperties = { ...tdStyle, textAlign: "end", fontVariantNumeric: "tabular-nums" };

export default ProductMovementHistoryPage;
