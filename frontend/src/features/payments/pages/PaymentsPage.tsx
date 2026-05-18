import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router";
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
} from "../../../components/ui/mvp";
import { getApiErrorMessage } from "../../../lib/api/errors";
import { theme } from "../../../styles/theme";
import { listPartners } from "../../partners/api/list-partners";
import type { Partner } from "../../partners/types/partner";
import { getAccounts } from "../api/accounts-api";
import type { AccountLookup } from "../api/accounts-api";
import { createPayment, getPayments, postPayment } from "../api/payments-api";
import type { CreatePaymentPayload, Payment } from "../types/payment";

type StatusFilter = "all" | Payment["status"];
type PaymentTypeFilter = "all" | Payment["payment_type"];
type PaymentMethodFilter = "all" | Payment["payment_method"];

const initialForm: CreatePaymentPayload = {
  partner: "",
  account: "",
  payment_type: "inbound",
  payment_method: "cash",
  amount: "",
  date: new Date().toISOString().slice(0, 10),
  reference: "",
  notes: "",
};
const searchStorageKey = "erp.payments.search";

function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [partners, setPartners] = useState<Partner[]>([]);
  const [accounts, setAccounts] = useState<AccountLookup[]>([]);
  const [partnersMap, setPartnersMap] = useState<Record<string, string>>({});
  const [accountsMap, setAccountsMap] = useState<Record<string, string>>({});
  const [form, setForm] = useState<CreatePaymentPayload>(initialForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [postingId, setPostingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [draftQuery, setDraftQuery] = useState(() => sessionStorage.getItem(searchStorageKey) || "");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [typeFilter, setTypeFilter] = useState<PaymentTypeFilter>("all");
  const [methodFilter, setMethodFilter] = useState<PaymentMethodFilter>("all");

  async function loadPayments() {
    try {
      setLoading(true);
      setError("");

      const [paymentsData, partnersData, accountsData] = await Promise.all([
        getPayments(),
        listPartners(),
        getAccounts(),
      ]);

      setPayments(Array.isArray(paymentsData) ? paymentsData : []);
      setPartners(Array.isArray(partnersData) ? partnersData : []);
      setAccounts(Array.isArray(accountsData) ? accountsData : []);
      setPartnersMap(buildPartnersMap(partnersData));
      setAccountsMap(buildAccountsMap(accountsData));
    } catch (err) {
      console.error("Payments load error:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPayments();
  }, []);

  const filteredPayments = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return payments.filter((payment) => {
      const partnerName = partnersMap[payment.partner] || payment.partner;
      const reference = payment.reference || "";
      const voucherNumber = payment.voucher_number || "";
      const matchesQuery =
        !normalizedQuery ||
        reference.toLowerCase().includes(normalizedQuery) ||
        voucherNumber.toLowerCase().includes(normalizedQuery) ||
        partnerName.toLowerCase().includes(normalizedQuery);
      const matchesStatus = statusFilter === "all" || payment.status === statusFilter;
      const matchesType = typeFilter === "all" || payment.payment_type === typeFilter;
      const matchesMethod = methodFilter === "all" || payment.payment_method === methodFilter;

      return matchesQuery && matchesStatus && matchesType && matchesMethod;
    });
  }, [methodFilter, partnersMap, payments, query, statusFilter, typeFilter]);

  const paymentSummary = getPaymentSummary(filteredPayments);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError("");

      await createPayment({
        ...form,
        partner: form.partner.trim(),
        account: form.account.trim(),
        amount: form.amount.trim(),
        reference: form.reference?.trim(),
        notes: form.notes?.trim(),
      });

      setForm(initialForm);
      await loadPayments();
    } catch (err) {
      console.error("Payment create error:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePostPayment(id: string) {
    try {
      setPostingId(id);
      setError("");

      await postPayment(id);
      await loadPayments();
    } catch (err) {
      console.error("Payment post error:", err);
      setError(getApiErrorMessage(err));
    } finally {
      setPostingId(null);
    }
  }

  function applySearch() {
    const nextQuery = draftQuery.trim();
    setQuery(nextQuery);
    sessionStorage.setItem(searchStorageKey, nextQuery);
  }

  function clearFilters() {
    setDraftQuery("");
    setQuery("");
    setStatusFilter("all");
    setTypeFilter("all");
    setMethodFilter("all");
    sessionStorage.removeItem(searchStorageKey);
  }

  return (
    <main style={pageStyle}>
      <PageHeader
        title="المدفوعات"
        subtitle="إنشاء دفعات واردة وصادرة ثم ترحيل المسودات عند الجاهزية."
      />

      <form onSubmit={handleSubmit} style={formCardStyle}>
        <div style={formHeaderStyle}>
          <h2 style={formTitleStyle}>إنشاء دفعة</h2>
          <p style={formSubtitleStyle}>سجل تحصيلات العملاء ومدفوعات الموردين كمستندات مسودة.</p>
        </div>

        <div style={paymentTypeGroupStyle}>
          <button
            type="button"
            onClick={() => setForm((current) => ({ ...current, payment_type: "inbound" }))}
            style={getPaymentTypeButtonStyle(form.payment_type === "inbound")}
          >
            <span style={paymentTypeTitleStyle}>وارد</span>
            <span style={paymentTypeHintStyle}>تحصيل من عميل</span>
          </button>

          <button
            type="button"
            onClick={() => setForm((current) => ({ ...current, payment_type: "outbound" }))}
            style={getPaymentTypeButtonStyle(form.payment_type === "outbound")}
          >
            <span style={paymentTypeTitleStyle}>صادر</span>
            <span style={paymentTypeHintStyle}>دفع إلى مورد</span>
          </button>
        </div>

        <div style={formGridStyle}>
          <label style={fieldStyle}>
            <span style={labelStyle}>الشريك</span>
            <select
              required
              value={form.partner}
              onChange={(event) => setForm((current) => ({ ...current, partner: event.target.value }))}
              style={inputStyle}
            >
              <option value="">اختر الشريك</option>
              {partners.map((partner) => (
                <option key={partner.id} value={partner.id}>
                  {partner.name}
                </option>
              ))}
            </select>
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>الحساب</span>
            <select
              required
              value={form.account}
              onChange={(event) => setForm((current) => ({ ...current, account: event.target.value }))}
              style={inputStyle}
            >
              <option value="">اختر الحساب</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {formatAccountLabel(account)}
                </option>
              ))}
            </select>
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>طريقة الدفع</span>
            <select
              value={form.payment_method}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  payment_method: event.target.value as CreatePaymentPayload["payment_method"],
                }))
              }
              style={inputStyle}
            >
              <option value="cash">نقدي</option>
              <option value="bank">بنك</option>
            </select>
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>المبلغ</span>
            <input
              required
              type="number"
              min="0.01"
              step="0.01"
              value={form.amount}
              onChange={(event) => setForm((current) => ({ ...current, amount: event.target.value }))}
              style={inputStyle}
            />
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>التاريخ</span>
            <input
              required
              type="date"
              value={form.date}
              onChange={(event) => setForm((current) => ({ ...current, date: event.target.value }))}
              style={inputStyle}
            />
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>المرجع</span>
            <input
              value={form.reference}
              onChange={(event) => setForm((current) => ({ ...current, reference: event.target.value }))}
              style={inputStyle}
            />
          </label>

          <label style={{ ...fieldStyle, gridColumn: "1 / -1" }}>
            <span style={labelStyle}>ملاحظات</span>
            <textarea
              value={form.notes}
              onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
              rows={2}
              style={{ ...inputStyle, resize: "vertical" }}
            />
          </label>
        </div>

        <div style={formActionsStyle}>
          <button type="submit" disabled={submitting} style={primaryButtonStyle}>
            {submitting ? "جاري الإنشاء..." : "إنشاء دفعة"}
          </button>
        </div>
      </form>

      <ErrorMessage message={error} />
      {loading && <LoadingState label="جاري تحميل المدفوعات..." />}

      {!loading && (
        <div style={workspaceStyle}>
          <section style={summaryGridStyle}>
            <MetricCard
              title="إجمالي الوارد"
              value={formatNumber(paymentSummary.received)}
              subtitle="دفعات واردة حسب الفلاتر"
              tone="success"
            />
            <MetricCard
              title="إجمالي الصادر"
              value={formatNumber(paymentSummary.paid)}
              subtitle="دفعات صادرة حسب الفلاتر"
              tone="danger"
            />
            <MetricCard
              title="دفعات مسودة"
              value={formatNumber(paymentSummary.drafts)}
              subtitle="بانتظار الترحيل"
              tone="warning"
            />
            <MetricCard
              title="دفعات مرحلة"
              value={formatNumber(paymentSummary.posted)}
              subtitle="مستندات دفع مرحلة"
              tone="info"
            />
          </section>

          <section style={tableCardStyle}>
            <div style={filtersBarStyle}>
              <SearchField
                id="payment-search"
                label="البحث"
                value={draftQuery}
                onChange={setDraftQuery}
                onSearch={applySearch}
                onClear={clearFilters}
                placeholder="مرجع الدفع أو الشريك"
              />

              <FilterSelect
                id="payment-status"
                label="الحالة"
                value={statusFilter}
                onChange={(value) => setStatusFilter(value as StatusFilter)}
                options={[
                  ["all", "الكل"],
                  ["draft", "مسودة"],
                  ["posted", "مرحلة"],
                  ["cancelled", "ملغاة"],
                ]}
              />

              <FilterSelect
                id="payment-type"
                label="نوع الدفع"
                value={typeFilter}
                onChange={(value) => setTypeFilter(value as PaymentTypeFilter)}
                options={[
                  ["all", "الكل"],
                  ["inbound", "وارد"],
                  ["outbound", "صادر"],
                ]}
              />

              <FilterSelect
                id="payment-method"
                label="الطريقة"
                value={methodFilter}
                onChange={(value) => setMethodFilter(value as PaymentMethodFilter)}
                options={[
                  ["all", "الكل"],
                  ["cash", "نقدي"],
                  ["bank", "بنك"],
                ]}
              />

              <div style={tableMetaStyle}>
                <strong>{filteredPayments.length}</strong>
                <span>من {payments.length} دفعة</span>
              </div>

              <ClearFiltersButton onClick={clearFilters} label="مسح" />
            </div>

            {filteredPayments.length === 0 ? (
              <div style={emptyWrapStyle}>
                <EmptyState title="لا توجد مدفوعات" message="عدّل الفلاتر أو أنشئ دفعة جديدة." />
              </div>
            ) : (
              <>
                <div style={tableWrapperStyle}>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        <th style={{ ...thStyle, minWidth: "150px" }}>رقم السند</th>
                        <th style={thStyle}>التاريخ</th>
                        <th style={thStyle}>النوع</th>
                        <th style={thStyle}>الطريقة</th>
                        <th style={thStyle}>الشريك</th>
                        <th style={thStyle}>الحساب</th>
                        <th style={{ ...thStyle, textAlign: "end" }}>المبلغ</th>
                        <th style={thStyle}>الحالة</th>
                        <th style={thStyle}>المرجع</th>
                        <th style={{ ...thStyle, minWidth: "220px", textAlign: "center" }}>الإجراءات</th>
                      </tr>
                    </thead>

                    <tbody>
                      {filteredPayments.map((payment) => (
                        <tr key={payment.id}>
                          <td style={tdStyle}>
                            <strong style={primaryCellTextStyle}>{payment.voucher_number || "-"}</strong>
                          </td>
                          <td style={tdStyle}>
                            <span style={mutedTextStyle}>{payment.date}</span>
                          </td>
                          <td style={tdStyle}>{formatPaymentType(payment.payment_type)}</td>
                          <td style={tdStyle}>{formatPaymentMethod(payment.payment_method)}</td>
                          <td style={tdStyle}>{partnersMap[payment.partner] || payment.partner}</td>
                          <td style={tdStyle}>{accountsMap[payment.account] || payment.account}</td>
                          <td style={{ ...tdStyle, textAlign: "end" }}>
                            <span style={amountTextStyle}>{payment.amount}</span>
                          </td>
                          <td style={tdStyle}>
                            <StatusBadge status={formatPaymentStatus(payment.status)} tone={getPaymentStatusTone(payment.status)} />
                          </td>
                          <td style={tdStyle}>{payment.reference || "-"}</td>
                          <td style={{ ...tdStyle, textAlign: "center" }}>
                            <div style={actionsStyle}>
                              <button type="button" disabled style={disabledActionStyle}>
                                عرض
                              </button>
                              {payment.status === "draft" && (
                                <button
                                  type="button"
                                  disabled={postingId === payment.id}
                                  onClick={() => handlePostPayment(payment.id)}
                                  style={{
                                    ...actionButtonStyle,
                                    opacity: postingId === payment.id ? 0.65 : 1,
                                    cursor: postingId === payment.id ? "not-allowed" : "pointer",
                                  }}
                                >
                                  {postingId === payment.id ? "جاري الترحيل..." : "ترحيل"}
                                </button>
                              )}
                              {payment.journal_entry && (
                                <Link
                                  to={`/accounting/journal-entries/${payment.journal_entry}`}
                                  style={actionLinkStyle}
                                >
                                  القيد
                                </Link>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={tableFooterStyle}>
                  <span>يتم تطبيق الفلاتر محلياً لأن واجهة المدفوعات الحالية ترجع قائمة مباشرة.</span>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </main>
  );
}

function FilterSelect({
  id,
  label,
  value,
  onChange,
  options,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
}) {
  return (
    <div style={filterGroupStyle}>
      <label style={filterLabelStyle} htmlFor={id}>
        {label}
      </label>
      <select id={id} value={value} onChange={(event) => onChange(event.target.value)} style={inputStyle}>
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
    </div>
  );
}

function buildPartnersMap(partners: Partner[]) {
  return partners.reduce<Record<string, string>>((current, partner) => {
    current[partner.id] = partner.name;
    return current;
  }, {});
}

function buildAccountsMap(accounts: AccountLookup[]) {
  return accounts.reduce<Record<string, string>>((current, account) => {
    current[account.id] = formatAccountLabel(account);
    return current;
  }, {});
}

function formatAccountLabel(account: AccountLookup) {
  return `${account.code} - ${account.name}`;
}

function formatPaymentType(paymentType: Payment["payment_type"]) {
  return paymentType === "inbound" ? "وارد" : "صادر";
}

function formatPaymentMethod(paymentMethod: Payment["payment_method"]) {
  return paymentMethod === "cash" ? "نقدي" : "بنك";
}

function formatPaymentStatus(status: Payment["status"]) {
  if (status === "posted") return "مرحلة";
  if (status === "cancelled") return "ملغاة";
  return "مسودة";
}

function getPaymentStatusTone(status: Payment["status"]) {
  if (status === "posted") return "success";
  if (status === "cancelled") return "danger";
  return "warning";
}

function getPaymentSummary(payments: Payment[]) {
  return payments.reduce(
    (summary, payment) => {
      const amount = Number(payment.amount || 0);

      if (payment.payment_type === "inbound") {
        summary.received += amount;
      } else {
        summary.paid += amount;
      }

      if (payment.status === "draft") {
        summary.drafts += 1;
      }

      if (payment.status === "posted") {
        summary.posted += 1;
      }

      return summary;
    },
    { received: 0, paid: 0, drafts: 0, posted: 0 }
  );
}

const pageStyle: React.CSSProperties = {
  background: "transparent",
  minHeight: "100%",
  minWidth: 0,
};

const workspaceStyle: React.CSSProperties = {
  display: "grid",
  gap: "16px",
};

const formCardStyle: React.CSSProperties = {
  background: "linear-gradient(145deg, rgba(255,255,255,0.94), rgba(236,254,255,0.38))",
  border: "1px solid rgba(255, 255, 255, 0.78)",
  borderRadius: "20px",
  marginBottom: "16px",
  overflow: "hidden",
  boxShadow: "0 18px 42px rgba(15, 23, 42, 0.07), inset 0 1px 0 rgba(255,255,255,0.86)",
  backdropFilter: "blur(22px) saturate(145%)",
};

const formHeaderStyle: React.CSSProperties = {
  padding: "14px 16px",
  borderBottom: `1px solid ${theme.colors.border}`,
};

const formTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "18px",
  color: theme.colors.textPrimary,
};

const formSubtitleStyle: React.CSSProperties = {
  margin: "4px 0 0",
  color: theme.colors.textSecondary,
  fontSize: "13px",
};

const paymentTypeGroupStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "10px",
  padding: "14px 16px 0",
};

function getPaymentTypeButtonStyle(isActive: boolean): React.CSSProperties {
  return {
    border: `1px solid ${isActive ? theme.colors.primary : theme.colors.border}`,
    background: isActive ? "rgba(14, 165, 164, 0.08)" : "#ffffff",
    color: theme.colors.textPrimary,
    borderRadius: "14px",
    padding: "10px 12px",
    textAlign: "left",
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    gap: "3px",
  };
}

const paymentTypeTitleStyle: React.CSSProperties = {
  fontWeight: 800,
  fontSize: "14px",
};

const paymentTypeHintStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "12px",
};

const formGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "12px",
  padding: "16px",
};

const fieldStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "6px",
};

const labelStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "12px",
  fontWeight: 700,
};

const inputStyle: React.CSSProperties = {
  height: "38px",
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "10px",
  padding: "0 11px",
  fontSize: "13px",
  color: theme.colors.textPrimary,
  background: "#ffffff",
};

const formActionsStyle: React.CSSProperties = {
  padding: "0 16px 16px",
  display: "flex",
  justifyContent: "flex-end",
};

const primaryButtonStyle: React.CSSProperties = {
  border: "none",
  background: theme.colors.primary,
  color: "#ffffff",
  minHeight: "36px",
  padding: "0 14px",
  borderRadius: "10px",
  fontWeight: 700,
  cursor: "pointer",
};

const summaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "14px",
};

const tableCardStyle: React.CSSProperties = {
  background: "linear-gradient(145deg, rgba(255,255,255,0.94), rgba(236,254,255,0.38))",
  border: "1px solid rgba(255, 255, 255, 0.78)",
  borderRadius: "20px",
  overflow: "hidden",
  boxShadow: "0 18px 42px rgba(15, 23, 42, 0.07), inset 0 1px 0 rgba(255,255,255,0.86)",
  backdropFilter: "blur(22px) saturate(145%)",
  minWidth: 0,
};

const filtersBarStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "minmax(220px, 1.4fr) repeat(3, minmax(130px, 0.7fr)) auto auto",
  gap: "12px",
  alignItems: "end",
  padding: "14px 16px",
  borderBottom: `1px solid ${theme.colors.border}`,
};

const filterGroupStyle: React.CSSProperties = {
  display: "grid",
  gap: "6px",
  minWidth: 0,
};

const filterLabelStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "12px",
  fontWeight: 700,
};

const tableMetaStyle: React.CSSProperties = {
  display: "grid",
  gap: "2px",
  justifyItems: "end",
  color: theme.colors.textSecondary,
  fontSize: "12px",
  whiteSpace: "nowrap",
};

const emptyWrapStyle: React.CSSProperties = {
  padding: "16px",
};

const tableWrapperStyle: React.CSSProperties = {
  maxHeight: "min(58vh, 620px)",
  overflow: "auto",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "separate",
  borderSpacing: 0,
  minWidth: "1120px",
};

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
  verticalAlign: "middle",
};

const primaryCellTextStyle: React.CSSProperties = {
  color: theme.colors.textPrimary,
  fontWeight: 700,
};

const mutedTextStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontWeight: 500,
};

const amountTextStyle: React.CSSProperties = {
  color: theme.colors.textPrimary,
  fontWeight: 800,
  fontVariantNumeric: "tabular-nums",
};

const actionsStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "6px",
  flexWrap: "wrap",
};

const actionLinkStyle: React.CSSProperties = {
  minHeight: "30px",
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "0 10px",
  borderRadius: "9px",
  border: `1px solid ${theme.colors.border}`,
  background: "#ffffff",
  color: theme.colors.primaryDark,
  textDecoration: "none",
  fontSize: "12px",
  fontWeight: 700,
};

const actionButtonStyle: React.CSSProperties = {
  ...actionLinkStyle,
  color: "#ffffff",
  background: theme.colors.primary,
  border: `1px solid ${theme.colors.primary}`,
};

const disabledActionStyle: React.CSSProperties = {
  ...actionLinkStyle,
  color: theme.colors.textSecondary,
  background: "rgba(248, 250, 252, 0.72)",
  cursor: "not-allowed",
  opacity: 0.65,
};

const tableFooterStyle: React.CSSProperties = {
  padding: "10px 16px",
  color: theme.colors.textSecondary,
  fontSize: "12px",
  borderTop: `1px solid ${theme.colors.border}`,
  background: "rgba(248, 250, 252, 0.66)",
};

export default PaymentsPage;
