import { useEffect, useState } from "react";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
  SectionCard,
} from "../../../components/ui/mvp";
import { getApiErrorMessage } from "../../../lib/api/errors";
import { theme } from "../../../styles/theme";
import { listPartners } from "../../partners/api/list-partners";
import type { Partner } from "../../partners/types/partner";
import { getAccounts } from "../../payments/api/accounts-api";
import type { AccountLookup } from "../../payments/api/accounts-api";
import { getGeneralLedger } from "../api/reports-api";
import type { GeneralLedgerFilters, GeneralLedgerRow } from "../api/reports-api";

const initialFilters: GeneralLedgerFilters = {
  start_date: "",
  end_date: "",
  account: "",
  partner: "",
};

function GeneralLedgerPage() {
  const [rows, setRows] = useState<GeneralLedgerRow[]>([]);
  const [accounts, setAccounts] = useState<AccountLookup[]>([]);
  const [partners, setPartners] = useState<Partner[]>([]);
  const [filters, setFilters] = useState<GeneralLedgerFilters>(initialFilters);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadReport(nextFilters = filters) {
    try {
      setLoading(true);
      setError("");
      const [reportRows, accountsData, partnersData] = await Promise.all([
        getGeneralLedger(nextFilters),
        getAccounts(),
        listPartners(),
      ]);

      setRows(reportRows);
      setAccounts(accountsData);
      setPartners(partnersData);
    } catch (err) {
      console.error("General ledger report error:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport(initialFilters);
  }, []);

  function updateFilter(key: keyof GeneralLedgerFilters, value: string) {
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
      <PageHeader title="دفتر الأستاذ العام" subtitle="عرض قيود الحسابات من تقرير الأستاذ العام." />

      <SectionCard>
        <form onSubmit={handleSubmit} style={filtersStyle}>
          <FilterInput label="من تاريخ" type="date" value={filters.start_date || ""} onChange={(value) => updateFilter("start_date", value)} />
          <FilterInput label="إلى تاريخ" type="date" value={filters.end_date || ""} onChange={(value) => updateFilter("end_date", value)} />
          <FilterSelect label="الحساب" value={filters.account || ""} onChange={(value) => updateFilter("account", value)}>
            <option value="">كل الحسابات</option>
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.code} - {account.name}
              </option>
            ))}
          </FilterSelect>
          <FilterSelect label="الشريك" value={filters.partner || ""} onChange={(value) => updateFilter("partner", value)}>
            <option value="">كل الشركاء</option>
            {partners.map((partner) => (
              <option key={partner.id} value={partner.id}>
                {partner.name}
              </option>
            ))}
          </FilterSelect>
          <div style={actionsStyle}>
            <button type="submit" style={primaryButtonStyle}>تطبيق</button>
            <button type="button" onClick={clearFilters} style={secondaryButtonStyle}>مسح</button>
          </div>
        </form>
      </SectionCard>

      <ErrorMessage message={error} />
      {loading && <LoadingState label="جاري تحميل دفتر الأستاذ..." />}

      {!loading && !error && (
        <SectionCard>
          {rows.length === 0 ? (
            <EmptyState title="لا توجد قيود" message="غيّر الفلاتر أو تأكد من وجود قيود مرحلة." />
          ) : (
            <div style={tableWrapperStyle}>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>التاريخ</th>
                    <th style={thStyle}>رقم القيد</th>
                    <th style={thStyle}>المرجع</th>
                    <th style={thStyle}>الحساب</th>
                    <th style={thStyle}>الشريك</th>
                    <th style={rightThStyle}>مدين</th>
                    <th style={rightThStyle}>دائن</th>
                    <th style={rightThStyle}>الرصيد الجاري</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, index) => (
                    <tr key={row.id || `${row.entry_number}-${index}`}>
                      <td style={tdStyle}>{row.date}</td>
                      <td style={tdStrongStyle}>{row.entry_number}</td>
                      <td style={tdStyle}>{row.reference || "-"}</td>
                      <td style={tdStyle}>{formatValue(row.account)}</td>
                      <td style={tdStyle}>{formatValue(row.partner)}</td>
                      <td style={rightTdStyle}>{row.debit}</td>
                      <td style={rightTdStyle}>{row.credit}</td>
                      <td style={rightTdStyle}>{row.running_balance}</td>
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
  return (
    <label style={fieldStyle}>
      <span style={labelStyle}>{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} style={inputStyle} />
    </label>
  );
}

function FilterSelect({ label, value, onChange, children }: { label: string; value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return (
    <label style={fieldStyle}>
      <span style={labelStyle}>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)} style={inputStyle}>
        {children}
      </select>
    </label>
  );
}

function formatValue(value: unknown) {
  if (!value) return "-";
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    return String(record.name || record.code || record.label || record.id || "-");
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

export default GeneralLedgerPage;
