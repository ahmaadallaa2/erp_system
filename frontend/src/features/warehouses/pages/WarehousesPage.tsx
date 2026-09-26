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
import { listWarehouses } from "../api/list-warehouses";
import type { Warehouse } from "../types/warehouse";

const searchStorageKey = "erp.warehouses.search";

function WarehousesPage() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [draftQuery, setDraftQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");

  useEffect(() => {
    async function loadWarehouses() {
      try {
        setLoading(true);
        setError("");

        const result = await listWarehouses();
        setWarehouses(Array.isArray(result) ? result : []);
      } catch (err) {
        console.error("Warehouses load error:", err);
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    loadWarehouses();
  }, []);

  const filteredWarehouses = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return warehouses.filter((warehouse) => {
      return (
        !normalizedQuery ||
        warehouse.name.toLowerCase().includes(normalizedQuery) ||
        warehouse.code.toLowerCase().includes(normalizedQuery)
      );
    });
  }, [warehouses, query]);

  const activeCount = filteredWarehouses.filter((warehouse) => warehouse.is_active).length;
  const branchCount = new Set(filteredWarehouses.map((warehouse) => warehouse.branch).filter(Boolean)).size;
  const typeCount = new Set(filteredWarehouses.map((warehouse) => warehouse.warehouse_type).filter(Boolean)).size;

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
      <PageHeader
        title="Warehouses"
        subtitle="Storage locations and branches used by inventory documents."
      />

      {loading && <LoadingState label="Loading warehouses..." />}
      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && (
        <div style={workspaceStyle}>
          <section style={summaryGridStyle}>
            <MetricCard title="Total Warehouses" value={formatNumber(filteredWarehouses.length)} tone="info" />
            <MetricCard title="Active Warehouses" value={formatNumber(activeCount)} tone="success" />
            <MetricCard title="Linked Branches" value={formatNumber(branchCount)} tone="neutral" />
            <MetricCard title="Warehouse Types" value={formatNumber(typeCount)} tone="warning" />
          </section>

          <section style={tableCardStyle}>
            <div style={filtersBarStyle}>
              <SearchField
                id="warehouse-search"
                value={draftQuery}
                onChange={setDraftQuery}
                onSearch={applySearch}
                onClear={clearFilters}
                placeholder="Warehouse name or code"
              />

              <div style={tableMetaStyle}>
                <strong>{filteredWarehouses.length}</strong>
                <span>of {warehouses.length} warehouses</span>
              </div>

              <ClearFiltersButton onClick={clearFilters} />
            </div>

            {filteredWarehouses.length === 0 ? (
              <div style={emptyWrapStyle}>
                <EmptyState title="No warehouses found" message="Adjust filters or create warehouses from the backend workflow." />
              </div>
            ) : (
              <div style={tableWrapperStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Code</th>
                      <th style={thStyle}>Warehouse Name</th>
                      <th style={thStyle}>Type</th>
                      <th style={thStyle}>Branch</th>
                      <th style={thStyle}>Address</th>
                      <th style={thStyle}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredWarehouses.map((warehouse) => (
                      <tr key={warehouse.id}>
                        <td style={tdStrongStyle}>{warehouse.code}</td>
                        <td style={tdStyle}>{warehouse.name}</td>
                        <td style={tdStyle}>{toBusinessLabel(warehouse.warehouse_type)}</td>
                        <td style={tdStyle}>{warehouse.branch || "-"}</td>
                        <td style={tdStyle}>{warehouse.address || "-"}</td>
                        <td style={tdStyle}>
                          <StatusBadge status={warehouse.is_active ? "active" : "inactive"} />
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
const tableStyle: React.CSSProperties = { width: "100%", borderCollapse: "separate", borderSpacing: 0, minWidth: "820px" };
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

export default WarehousesPage;
