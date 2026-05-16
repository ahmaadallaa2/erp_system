import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router";
import axios from "axios";
import { theme } from "../../../styles/theme";
import { listPartners } from "../../partners/api/list-partners";
import type { Partner } from "../../partners/types/partner";
import { getAccounts } from "../api/accounts-api";
import type { AccountLookup } from "../api/accounts-api";
import { createPayment, getPayments, postPayment } from "../api/payments-api";
import type { CreatePaymentPayload, Payment } from "../types/payment";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  MetricCard,
  PageHeader,
  StatusBadge,
  formatNumber,
  toBusinessLabel,
} from "../../../components/ui/mvp";

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
      setError("Failed to load payments.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPayments();
  }, []);

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
      setError(getApiErrorMessage(err, "Failed to create payment."));
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
      setError(getApiErrorMessage(err, "Failed to post payment."));
    } finally {
      setPostingId(null);
    }
  }

  const paymentSummary = getPaymentSummary(payments);

  return (
    <main style={pageStyle}>
      <PageHeader
        title="Payments"
        subtitle="Create draft customer receipts and supplier payments, then post them."
      />

      <form onSubmit={handleSubmit} style={formCardStyle}>
        <div style={formHeaderStyle}>
          <h2 style={formTitleStyle}>New Draft Payment</h2>
          <p style={formSubtitleStyle}>
            Select Receive Payment for inbound customer cash/bank receipts, or Make
            Payment for outbound supplier payments.
          </p>
        </div>

        <div style={paymentTypeGroupStyle}>
          <button
            type="button"
            onClick={() =>
              setForm((current) => ({ ...current, payment_type: "inbound" }))
            }
            style={getPaymentTypeButtonStyle(form.payment_type === "inbound")}
          >
            <span style={paymentTypeTitleStyle}>Receive Payment</span>
            <span style={paymentTypeHintStyle}>Inbound from customer</span>
          </button>

          <button
            type="button"
            onClick={() =>
              setForm((current) => ({ ...current, payment_type: "outbound" }))
            }
            style={getPaymentTypeButtonStyle(form.payment_type === "outbound")}
          >
            <span style={paymentTypeTitleStyle}>Make Payment</span>
            <span style={paymentTypeHintStyle}>Outbound to supplier</span>
          </button>
        </div>

        <div style={formGridStyle}>
          <label style={fieldStyle}>
            <span style={labelStyle}>Partner</span>
            <select
              required
              value={form.partner}
              onChange={(event) =>
                setForm((current) => ({ ...current, partner: event.target.value }))
              }
              style={inputStyle}
            >
              <option value="">Select partner</option>
              {partners.map((partner) => (
                <option key={partner.id} value={partner.id}>
                  {partner.name}
                </option>
              ))}
            </select>
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>Account</span>
            <select
              required
              value={form.account}
              onChange={(event) =>
                setForm((current) => ({ ...current, account: event.target.value }))
              }
              style={inputStyle}
            >
              <option value="">Select account</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {formatAccountLabel(account)}
                </option>
              ))}
            </select>
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>Payment Method</span>
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
              <option value="cash">Cash Account</option>
              <option value="bank">Bank Account</option>
            </select>
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>Amount</span>
            <input
              required
              type="number"
              min="0.01"
              step="0.01"
              value={form.amount}
              onChange={(event) =>
                setForm((current) => ({ ...current, amount: event.target.value }))
              }
              style={inputStyle}
            />
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>Date</span>
            <input
              required
              type="date"
              value={form.date}
              onChange={(event) =>
                setForm((current) => ({ ...current, date: event.target.value }))
              }
              style={inputStyle}
            />
          </label>

          <label style={fieldStyle}>
            <span style={labelStyle}>Reference</span>
            <input
              value={form.reference}
              onChange={(event) =>
                setForm((current) => ({ ...current, reference: event.target.value }))
              }
              style={inputStyle}
            />
          </label>

          <label style={{ ...fieldStyle, gridColumn: "1 / -1" }}>
            <span style={labelStyle}>Notes</span>
            <textarea
              value={form.notes}
              onChange={(event) =>
                setForm((current) => ({ ...current, notes: event.target.value }))
              }
              rows={3}
              style={{ ...inputStyle, resize: "vertical" }}
            />
          </label>
        </div>

        <div style={formActionsStyle}>
          <button type="submit" disabled={submitting} style={primaryButtonStyle}>
            {submitting ? "Creating..." : "Create Draft Payment"}
          </button>
        </div>
      </form>

      {loading && <LoadingState label="Loading payments..." />}

      {!loading && <ErrorMessage message={error} />}

      {!loading && !error && payments.length > 0 && (
        <div style={summaryGridStyle}>
          <MetricCard
            title="Total Received"
            value={formatNumber(paymentSummary.received)}
            subtitle="Inbound posted and draft payments"
            tone="success"
          />
          <MetricCard
            title="Total Paid"
            value={formatNumber(paymentSummary.paid)}
            subtitle="Outbound posted and draft payments"
            tone="danger"
          />
          <MetricCard
            title="Draft Payments"
            value={formatNumber(paymentSummary.drafts)}
            subtitle="Waiting to be posted"
            tone="warning"
          />
        </div>
      )}

      {!loading && !error && payments.length === 0 && (
        <EmptyState
          title="No payments found"
          message="Create your first draft payment above."
        />
      )}

      {!loading && !error && payments.length > 0 && (
        <div style={tableCardStyle}>
          <div style={tableHeaderBarStyle}>
            <div>
              <h2 style={tableTitleStyle}>Payments List</h2>
              <p style={tableSubtitleStyle}>Total payments: {payments.length}</p>
            </div>
          </div>

          <div style={tableWrapperStyle}>
            <table style={tableStyle}>
              <thead>
                <tr style={tableHeadRowStyle}>
                  <th style={{ ...thStyle, minWidth: "160px" }}>Voucher Number</th>
                  <th style={thStyle}>Date</th>
                  <th style={thStyle}>Type</th>
                  <th style={thStyle}>Method</th>
                  <th style={thStyle}>Partner</th>
                  <th style={thStyle}>Account</th>
                  <th style={{ ...thStyle, textAlign: "right" }}>Amount</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Reference</th>
                  <th style={{ ...thStyle, textAlign: "center" }}>Actions</th>
                </tr>
              </thead>

              <tbody>
                {payments.map((payment, index) => (
                  <tr key={payment.id} style={getRowStyle(index)}>
                    <td style={tdStyle}>
                      <span style={primaryCellTextStyle}>
                        {payment.voucher_number || "-"}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span style={mutedTextStyle}>{payment.date}</span>
                    </td>
                    <td style={tdStyle}>{formatPaymentType(payment.payment_type)}</td>
                    <td style={tdStyle}>{toBusinessLabel(payment.payment_method)}</td>
                    <td style={tdStyle}>
                      {partnersMap[payment.partner] || payment.partner}
                    </td>
                    <td style={tdStyle}>
                      {accountsMap[payment.account] || payment.account}
                    </td>
                    <td style={{ ...tdStyle, textAlign: "right" }}>
                      <span style={amountTextStyle}>{payment.amount}</span>
                    </td>
                    <td style={tdStyle}>
                      <StatusBadge status={payment.status} />
                    </td>
                    <td style={tdStyle}>{payment.reference || "-"}</td>
                    <td style={{ ...tdStyle, textAlign: "center" }}>
                      {payment.status === "draft" ? (
                        <button
                          type="button"
                          disabled={postingId === payment.id}
                          onClick={() => handlePostPayment(payment.id)}
                          style={secondaryButtonStyle}
                        >
                          {postingId === payment.id ? "Posting..." : "Post"}
                        </button>
                      ) : payment.journal_entry ? (
                        <Link
                          to={`/accounting/journal-entries/${payment.journal_entry}`}
                          style={secondaryButtonStyle}
                        >
                          View Journal Entry
                        </Link>
                      ) : (
                        <span style={mutedTextStyle}>-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
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
  return paymentType === "inbound" ? "Receive Payment" : "Make Payment";
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

      return summary;
    },
    { received: 0, paid: 0, drafts: 0 }
  );
}

function getApiErrorMessage(error: unknown, fallback: string) {
  if (!axios.isAxiosError(error)) {
    return fallback;
  }

  const detail = error.response?.data;
  const message = formatApiErrorDetail(detail);

  return message ? `${fallback}: ${message}` : fallback;
}

function formatApiErrorDetail(detail: unknown): string {
  if (!detail) {
    return "";
  }

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail.map(formatApiErrorDetail).filter(Boolean).join(" ");
  }

  if (typeof detail === "object") {
    return Object.entries(detail)
      .map(([key, value]) => {
        const message = formatApiErrorDetail(value);
        return message ? `${key}: ${message}` : "";
      })
      .filter(Boolean)
      .join(" ");
  }

  return String(detail);
}

const pageStyle: React.CSSProperties = {
  background: theme.colors.background,
};

const formCardStyle: React.CSSProperties = {
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "16px",
  marginBottom: "24px",
  overflow: "hidden",
};

const summaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "16px",
  marginBottom: "20px",
};

const formHeaderStyle: React.CSSProperties = {
  padding: "18px 20px",
  borderBottom: `1px solid ${theme.colors.border}`,
};

const formTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "18px",
  color: theme.colors.textPrimary,
};

const formSubtitleStyle: React.CSSProperties = {
  margin: "6px 0 0",
  color: theme.colors.textSecondary,
  fontSize: "13px",
};

const paymentTypeGroupStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "12px",
  padding: "18px 20px 0",
};

function getPaymentTypeButtonStyle(isActive: boolean): React.CSSProperties {
  return {
    border: `1px solid ${isActive ? theme.colors.primary : theme.colors.border}`,
    background: isActive ? "rgba(14, 165, 164, 0.08)" : "#ffffff",
    color: theme.colors.textPrimary,
    borderRadius: "8px",
    padding: "12px",
    textAlign: "left",
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
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
  gap: "16px",
  padding: "20px",
};

const fieldStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "6px",
};

const labelStyle: React.CSSProperties = {
  color: theme.colors.textSecondary,
  fontSize: "13px",
  fontWeight: 700,
};

const inputStyle: React.CSSProperties = {
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "8px",
  padding: "10px 12px",
  fontSize: "14px",
  color: theme.colors.textPrimary,
  background: "#ffffff",
};

const formActionsStyle: React.CSSProperties = {
  padding: "0 20px 20px",
  display: "flex",
  justifyContent: "flex-end",
};

const primaryButtonStyle: React.CSSProperties = {
  border: "none",
  background: theme.colors.primary,
  color: "#ffffff",
  padding: "10px 16px",
  borderRadius: "10px",
  fontWeight: 700,
  cursor: "pointer",
};

const secondaryButtonStyle: React.CSSProperties = {
  border: `1px solid ${theme.colors.primary}`,
  background: "#ffffff",
  color: theme.colors.primaryDark,
  padding: "7px 12px",
  borderRadius: "8px",
  fontWeight: 700,
  cursor: "pointer",
  textDecoration: "none",
};

const tableCardStyle: React.CSSProperties = {
  background: theme.colors.surface,
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "16px",
  overflow: "hidden",
  boxShadow: "0 10px 30px rgba(15, 23, 42, 0.05)",
};

const tableHeaderBarStyle: React.CSSProperties = {
  padding: "18px 20px",
  borderBottom: `1px solid ${theme.colors.border}`,
  background: "linear-gradient(180deg, rgba(14,165,164,0.04), rgba(14,165,164,0.01))",
};

const tableTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: "18px",
  color: theme.colors.textPrimary,
};

const tableSubtitleStyle: React.CSSProperties = {
  margin: "6px 0 0",
  fontSize: "13px",
  color: theme.colors.textSecondary,
};

const tableWrapperStyle: React.CSSProperties = {
  overflowX: "auto",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "separate",
  borderSpacing: 0,
};

const tableHeadRowStyle: React.CSSProperties = {
  background: "#f8fafc",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "14px 16px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "13px",
  fontWeight: 700,
  color: theme.colors.textSecondary,
  whiteSpace: "nowrap",
};

const tdStyle: React.CSSProperties = {
  padding: "16px",
  borderBottom: `1px solid ${theme.colors.border}`,
  fontSize: "14px",
  color: theme.colors.textPrimary,
  verticalAlign: "middle",
};

function getRowStyle(index: number): React.CSSProperties {
  return {
    background: index % 2 === 0 ? "#ffffff" : "#fbfdff",
  };
}

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
  fontWeight: 700,
  fontVariantNumeric: "tabular-nums",
};

export default PaymentsPage;
