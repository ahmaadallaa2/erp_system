import { useEffect, useState } from "react";
import { EmptyState, ErrorMessage, LoadingState, PageHeader, SectionCard, StatusBadge } from "../../../components/ui/mvp";
import { getApiErrorMessage } from "../../../lib/api/errors";
import { theme } from "../../../styles/theme";
import { listProducts } from "../../products/api/list-products";
import type { Product } from "../../products/types/product";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import type { Warehouse } from "../../warehouses/types/warehouse";
import { getWarehouseBalanceReport } from "../api/reports-api";
import type { WarehouseBalanceFilters, WarehouseBalanceReportRow } from "../api/reports-api";

const initialFilters: WarehouseBalanceFilters = {
  warehouse: "",
  product: "",
  low_stock: "",
};

function WarehouseBalancesReportPage() {
  const [rows, setRows] = useState<WarehouseBalanceReportRow[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [filters, setFilters] = useState<WarehouseBalanceFilters>(initialFilters);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadReport(nextFilters = filters) {
    try {
      setLoading(true);
      setError("");
      const [reportRows, productsData, warehousesData] = await Promise.all([
        getWarehouseBalanceReport(nextFilters),
        listProducts(),
        listWarehouses(),
      ]);

      setRows(reportRows);
      setProducts(productsData);
      setWarehouses(warehousesData);
    } catch (err) {
      console.error("Warehouse balance report error:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport(initialFilters);
  }, []);

  function updateFilter(key: keyof WarehouseBalanceFilters, value: string) {
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
      <PageHeader title="أرصدة المستودعات" subtitle="تقرير أرصدة المنتجات والقيمة التقديرية حسب المستودع." />

      <SectionCard>
        <form onSubmit={handleSubmit} style={filtersStyle}>
          <FilterSelect label="المستودع" value={filters.warehouse || ""} onChange={(value) => updateFilter("warehouse", value)}>
            <option value="">كل المستودعات</option>
            {warehouses.map((warehouse) => (
              <option key={warehouse.id} value={warehouse.id}>{warehouse.code} - {warehouse.name}</option>
            ))}
          </FilterSelect>
          <FilterSelect label="المنتج" value={filters.product || ""} onChange={(value) => updateFilter("product", value)}>
            <option value="">كل المنتجات</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>{product.sku} - {product.name}</option>
            ))}
          </FilterSelect>
          <FilterSelect label="المخزون المنخفض" value={filters.low_stock || ""} onChange={(value) => updateFilter("low_stock", value)}>
            <option value="">الكل</option>
            <option value="true">منخفض فقط</option>
            <option value="false">غير منخفض</option>
          </FilterSelect>
          <div style={actionsStyle}>
            <button type="submit" style={primaryButtonStyle}>تطبيق</button>
            <button type="button" onClick={clearFilters} style={secondaryButtonStyle}>مسح</button>
          </div>
        </form>
      </SectionCard>

      <ErrorMessage message={error} />
      {loading && <LoadingState label="جاري تحميل أرصدة المستودعات..." />}

      {!loading && !error && (
        <SectionCard>
          {rows.length === 0 ? (
            <EmptyState title="لا توجد أرصدة" message="غيّر الفلاتر أو تأكد من وجود أرصدة مخزون." />
          ) : (
            <div style={tableWrapperStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>المستودع</th>
                    <th style={thStyle}>المنتج</th>
                    <th style={rightThStyle}>الكمية</th>
                    <th style={rightThStyle}>حد إعادة الطلب</th>
                    <th style={thStyle}>منخفض</th>
                    <th style={rightThStyle}>متوسط التكلفة</th>
                    <th style={rightThStyle}>القيمة التقديرية</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={row.id || `${formatValue(row.warehouse)}-${formatValue(row.product)}-${index}`}>
                      <td style={tdStyle}>{formatValue(row.warehouse)}</td>
                      <td style={tdStrongStyle}>{formatValue(row.product)}</td>
                      <td style={rightTdStyle}>{row.quantity}</td>
                      <td style={rightTdStyle}>{row.reorder_point}</td>
                      <td style={tdStyle}>
                        <StatusBadge status={row.low_stock ? "منخفض" : "طبيعي"} tone={row.low_stock ? "warning" : "success"} />
                      </td>
                      <td style={rightTdStyle}>{row.average_cost}</td>
                      <td style={rightTdStyle}>{row.estimated_value}</td>
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

function FilterSelect({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return <label style={fieldStyle}><span style={labelStyle}>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)} style={inputStyle}>{children}</select></label>;
}

function formatValue(value: unknown) {
  if (!value) return "-";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    return String(record.name || record.code || record.sku || record.id || "-");
  }
  return "-";
}

const pageStyle: React.CSSProperties = { display: "grid", gap: "16px", minWidth: 0 };
const filtersStyle: React.CSSProperties = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr)) auto", gap: "12px", alignItems: "end" };
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

export default WarehouseBalancesReportPage;
