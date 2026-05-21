import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import {
  ComparisonBar,
  EmptyState,
  ErrorMessage,
  LoadingState,
  MetricCard,
  PageHeader,
  ProgressBar,
  SectionCard,
  StatusBadge,
  formatNumber,
} from "../../../components/ui/mvp";
import { getPayments } from "../../payments/api/payments-api";
import type { Payment } from "../../payments/types/payment";
import { listPurchaseInvoices } from "../../purchase-invoices/api/list-purchase-invoices";
import type { PurchaseInvoice } from "../../purchase-invoices/types/purchase-invoice";
import { listSalesInvoices } from "../../sales-invoices/api/list-sales-invoices";
import type { SalesInvoice } from "../../sales-invoices/types/sales-invoice";
import { listStockBalances } from "../../stock-balances/api/list-stock-balances";
import type { StockBalance } from "../../stock-balances/types/stock-balance";
import { theme } from "../../../styles/theme";
import { getDashboardSummary } from "../api/dashboard-api";
import type { DashboardSummary } from "../api/dashboard-api";

type SecondaryData = {
  payments: Payment[];
  salesInvoices: SalesInvoice[];
  purchaseInvoices: PurchaseInvoice[];
  stockBalances: StockBalance[];
};

const emptySecondaryData: SecondaryData = {
  payments: [],
  salesInvoices: [],
  purchaseInvoices: [],
  stockBalances: [],
};

function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [secondaryData, setSecondaryData] = useState<SecondaryData>(emptySecondaryData);
  const [isLoading, setIsLoading] = useState(true);
  const [secondaryLoading, setSecondaryLoading] = useState(true);
  const [error, setError] = useState("");
  const [secondaryError, setSecondaryError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      setIsLoading(true);
      setSecondaryLoading(true);
      setError("");
      setSecondaryError("");

      try {
        const data = await getDashboardSummary();
        setSummary(data);
      } catch (err) {
        console.error("Dashboard summary error:", err);
        setError("تعذر تحميل ملخص لوحة التحكم.");
      } finally {
        setIsLoading(false);
      }

      const [paymentsResult, salesResult, purchasesResult, stockResult] = await Promise.allSettled([
        getPayments(),
        listSalesInvoices(),
        listPurchaseInvoices(),
        listStockBalances(),
      ]);

      setSecondaryData({
        payments: paymentsResult.status === "fulfilled" && Array.isArray(paymentsResult.value) ? paymentsResult.value : [],
        salesInvoices: salesResult.status === "fulfilled" && Array.isArray(salesResult.value) ? salesResult.value : [],
        purchaseInvoices:
          purchasesResult.status === "fulfilled" && Array.isArray(purchasesResult.value) ? purchasesResult.value : [],
        stockBalances: stockResult.status === "fulfilled" && Array.isArray(stockResult.value) ? stockResult.value : [],
      });

      if ([paymentsResult, salesResult, purchasesResult, stockResult].some((result) => result.status === "rejected")) {
        setSecondaryError("بعض مؤشرات التشغيل غير متاحة حالياً، وتم عرض البيانات المتوفرة فقط.");
      }

      setSecondaryLoading(false);
    }

    loadDashboard();
  }, []);

  const metrics = useMemo(() => {
    const totalSales = toNumber(summary?.total_sales);
    const totalPurchases = toNumber(summary?.total_purchases);
    const receivables = toNumber(summary?.customers_receivable);
    const payables = toNumber(summary?.suppliers_payable);
    const inventoryQuantity = toNumber(summary?.inventory_quantity);
    const inventoryItems = toNumber(summary?.inventory_items);
    const lowStockProducts = toNumber(summary?.low_stock_products);

    return {
      totalSales,
      totalPurchases,
      grossDifference: totalSales - totalPurchases,
      receivables,
      payables,
      inventoryQuantity,
      inventoryItems,
      lowStockProducts,
    };
  }, [summary]);

  const paymentsSummary = useMemo(() => getPaymentsSummary(secondaryData.payments), [secondaryData.payments]);
  const salesStatus = useMemo(() => getStatusSummary(secondaryData.salesInvoices), [secondaryData.salesInvoices]);
  const purchaseStatus = useMemo(() => getStatusSummary(secondaryData.purchaseInvoices), [secondaryData.purchaseInvoices]);
  const lowStockRows = useMemo(
    () =>
      secondaryData.stockBalances
        .filter((balance) => Number(balance.quantity || 0) <= Number(balance.reorder_point || 0))
        .slice(0, 5),
    [secondaryData.stockBalances]
  );

  return (
    <main style={pageStyle}>
      <div style={breadcrumbStyle}>
        <strong>لوحة التحكم</strong>
        <span>/</span>
        <span>الإدارة</span>
      </div>

      <PageHeader
        title="لوحة التحكم"
        subtitle="متابعة مؤشرات الشركة والعمليات الرئيسية"
        note={<span>Current period: All time</span>}
      />

      <ErrorMessage message={error} />
      {isLoading && <LoadingState label="جاري تحميل ملخص لوحة التحكم..." />}

      {!isLoading && !error && (
        <div style={dashboardStackStyle}>
          <section style={kpiGridStyle}>
            <KpiLink to="/sales-invoices">
              <MetricCard title="إجمالي المبيعات" value={formatNumber(metrics.totalSales)} subtitle="فواتير مبيعات مرحلة" tone="info" accentColor="#14B8D4" />
            </KpiLink>
            <KpiLink to="/purchase-invoices">
              <MetricCard title="إجمالي المشتريات" value={formatNumber(metrics.totalPurchases)} subtitle="فواتير شراء مرحلة" tone="success" accentColor="#10B981" />
            </KpiLink>
            <KpiLink to="/payments">
              <MetricCard title="مستحقات العملاء" value={formatNumber(metrics.receivables)} subtitle="المبيعات ناقص المقبوضات" tone="warning" accentColor="#F59E0B" />
            </KpiLink>
            <KpiLink to="/payments">
              <MetricCard title="مستحقات الموردين" value={formatNumber(metrics.payables)} subtitle="المشتريات ناقص المدفوعات" tone="danger" accentColor="#EF4444" />
            </KpiLink>
            <KpiLink to="/stock-balances">
              <MetricCard title="كمية المخزون" value={formatNumber(metrics.inventoryQuantity)} subtitle={`${formatNumber(metrics.inventoryItems)} منتج مخزني`} tone="neutral" accentColor="#6366F1" />
            </KpiLink>
            <KpiLink to="/stock-balances">
              <MetricCard title="منتجات منخفضة المخزون" value={formatNumber(metrics.lowStockProducts)} subtitle="حسب حد إعادة الطلب" tone={metrics.lowStockProducts > 0 ? "warning" : "success"} accentColor="#F59E0B" />
            </KpiLink>
            <div style={grossCardStyle(metrics.grossDifference)}>
              <span>Gross Difference</span>
              <strong>{formatNumber(metrics.grossDifference)}</strong>
              <small>إجمالي المبيعات - إجمالي المشتريات</small>
            </div>
          </section>

          <ErrorMessage message={secondaryError} />
          {secondaryLoading && <LoadingState label="جاري تحميل مؤشرات التشغيل..." />}

          <section style={dashboardGridStyle}>
            <DashboardGridItem span={6}>
              <SectionCard title="المبيعات مقابل المشتريات" subtitle="مقارنة إجمالية من ملخص الداشبورد">
                <ComparisonBar
                  label="Sales vs Purchases"
                  leftLabel="المبيعات"
                  leftValue={metrics.totalSales}
                  rightLabel="المشتريات"
                  rightValue={metrics.totalPurchases}
                />
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={6}>
              <SectionCard title="المستحقات" subtitle="مقارنة مستحقات العملاء والموردين">
                <ComparisonBar
                  label="Receivables vs Payables"
                  leftLabel="مستحقات العملاء"
                  leftValue={metrics.receivables}
                  rightLabel="مستحقات الموردين"
                  rightValue={metrics.payables}
                />
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="صحة المخزون" subtitle="نسبة المنتجات منخفضة المخزون">
                <div style={cardStackStyle}>
                  <ProgressBar
                    label="منتجات سليمة"
                    value={Math.max(metrics.inventoryItems - metrics.lowStockProducts, 0)}
                    max={Math.max(metrics.inventoryItems, 1)}
                    tone="success"
                  />
                  <ProgressBar
                    label="منتجات منخفضة"
                    value={metrics.lowStockProducts}
                    max={Math.max(metrics.inventoryItems, 1)}
                    tone={metrics.lowStockProducts > 0 ? "warning" : "success"}
                  />
                </div>
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="ملخص المدفوعات" subtitle="من صفحة المدفوعات الحالية">
                <div style={miniGridStyle}>
                  <MetricMini label="إجمالي المقبوض" value={paymentsSummary.received} />
                  <MetricMini label="إجمالي المدفوع" value={paymentsSummary.paid} />
                  <MetricMini label="مسودات" value={paymentsSummary.drafts} />
                  <MetricMini label="مرحلة" value={paymentsSummary.posted} />
                </div>
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="إجراءات سريعة" subtitle="اختصارات تشغيلية">
                <div style={quickActionsGridStyle}>
                  <QuickAction to="/sales-invoices/new" label="فاتورة مبيعات جديدة" />
                  <QuickAction to="/purchase-invoices/new" label="فاتورة شراء جديدة" />
                  <QuickAction to="/payments" label="المدفوعات" />
                  <QuickAction to="/products" label="المنتجات" />
                  <QuickAction to="/stock-balances" label="أرصدة المخزون" />
                  <QuickAction to="/general-ledger" label="دفتر الأستاذ" />
                </div>
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="حالة فواتير المبيعات" subtitle="تجميع من فواتير المبيعات">
                <StatusSummary draft={salesStatus.draft} posted={salesStatus.posted} cancelled={salesStatus.cancelled} />
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="حالة فواتير الشراء" subtitle="تجميع من فواتير الشراء">
                <StatusSummary draft={purchaseStatus.draft} posted={purchaseStatus.posted} cancelled={purchaseStatus.cancelled} />
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="تنبيهات المخزون" subtitle="أول 5 منتجات منخفضة حسب الرصيد الحالي">
                {lowStockRows.length === 0 ? (
                  <EmptyState title="لا توجد تنبيهات" message="لا توجد أرصدة منخفضة متاحة حالياً." />
                ) : (
                  <div style={lowStockListStyle}>
                    {lowStockRows.map((balance) => (
                      <Link key={balance.id} to="/stock-balances" style={lowStockRowStyle}>
                        <div>
                          <strong>{balance.product}</strong>
                          <span>{balance.warehouse}</span>
                        </div>
                        <div style={lowStockNumbersStyle}>
                          <strong>{balance.quantity}</strong>
                          <span>حد الطلب: {balance.reorder_point}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </SectionCard>
            </DashboardGridItem>
          </section>
        </div>
      )}
    </main>
  );
}

function KpiLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link to={to} style={kpiLinkStyle}>
      {children}
    </Link>
  );
}

function QuickAction({ to, label }: { to: string; label: string }) {
  return (
    <Link to={to} style={quickActionStyle}>
      <span style={quickActionDotStyle} />
      <span>{label}</span>
    </Link>
  );
}

function MetricMini({ label, value }: { label: string; value: number }) {
  return (
    <div style={metricMiniStyle}>
      <span>{label}</span>
      <strong>{formatNumber(value)}</strong>
    </div>
  );
}

function StatusSummary({ draft, posted, cancelled }: { draft: number; posted: number; cancelled: number }) {
  return (
    <div style={statusSummaryStyle}>
      <StatusLine label="مسودة" value={draft} status="draft" />
      <StatusLine label="مرحلة" value={posted} status="posted" />
      <StatusLine label="ملغاة" value={cancelled} status="cancelled" />
    </div>
  );
}

function StatusLine({ label, value, status }: { label: string; value: number; status: string }) {
  return (
    <div style={statusLineStyle}>
      <StatusBadge status={label} tone={status === "posted" ? "success" : status === "cancelled" ? "danger" : "warning"} />
      <strong>{formatNumber(value)}</strong>
    </div>
  );
}

function DashboardGridItem({
  span,
  children,
}: {
  span: 3 | 4 | 6;
  children: React.ReactNode;
}) {
  return (
    <div className="erp-dashboard-grid-item" style={{ gridColumn: `span ${span}` }}>
      {children}
    </div>
  );
}

function getPaymentsSummary(payments: Payment[]) {
  return payments.reduce(
    (summary, payment) => {
      const amount = toNumber(payment.amount);

      if (payment.payment_type === "inbound") summary.received += amount;
      if (payment.payment_type === "outbound") summary.paid += amount;
      if (payment.status === "draft") summary.drafts += 1;
      if (payment.status === "posted") summary.posted += 1;

      return summary;
    },
    { received: 0, paid: 0, drafts: 0, posted: 0 }
  );
}

function getStatusSummary(items: Array<{ status: string }>) {
  return items.reduce(
    (summary, item) => {
      if (item.status === "draft") summary.draft += 1;
      if (item.status === "posted") summary.posted += 1;
      if (item.status === "cancelled") summary.cancelled += 1;
      return summary;
    },
    { draft: 0, posted: 0, cancelled: 0 }
  );
}

function toNumber(value: number | string | undefined | null) {
  const numeric = Number(value || 0);
  return Number.isFinite(numeric) ? numeric : 0;
}

const pageStyle: React.CSSProperties = {
  background: "transparent",
  minHeight: "100%",
  maxWidth: "1600px",
  margin: "0 auto",
  padding: "0",
  boxSizing: "border-box",
};

const breadcrumbStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  marginBottom: "4px",
  color: "#64748b",
  fontSize: "12px",
};

const dashboardStackStyle: React.CSSProperties = {
  display: "grid",
  gap: "16px",
};

const kpiGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
  gap: "14px",
};

const dashboardGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(12, minmax(0, 1fr))",
  gap: "16px",
};

const kpiLinkStyle: React.CSSProperties = {
  color: "inherit",
  textDecoration: "none",
  minWidth: 0,
};

function grossCardStyle(value: number): React.CSSProperties {
  return {
    background: "linear-gradient(145deg, rgba(255,255,255,0.94), rgba(236,254,255,0.48))",
    border: "1px solid rgba(255, 255, 255, 0.82)",
    borderTop: `4px solid ${value >= 0 ? "#10B981" : "#EF4444"}`,
    borderRadius: "20px",
    padding: "16px",
    boxShadow: "0 18px 42px rgba(15, 23, 42, 0.075), inset 0 1px 0 rgba(255,255,255,0.9)",
    display: "grid",
    gap: "8px",
  };
}

const cardStackStyle: React.CSSProperties = {
  display: "grid",
  gap: "14px",
  minHeight: "118px",
  alignContent: "center",
};

const miniGridStyle: React.CSSProperties = {
  display: "grid",
  gap: "10px",
};

const metricMiniStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: "16px",
  padding: "11px 12px",
  borderRadius: "12px",
  background: "#f8fafc",
  border: `1px solid ${theme.colors.border}`,
  color: "#475569",
  fontSize: "13px",
};

const quickActionsGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))",
  gap: "10px",
};

const quickActionStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "10px",
  padding: "10px",
  borderRadius: "12px",
  border: `1px solid ${theme.colors.border}`,
  background: "#f8fafc",
  color: "#020617",
  textDecoration: "none",
  fontSize: "13px",
  fontWeight: 800,
};

const quickActionDotStyle: React.CSSProperties = {
  width: "9px",
  height: "9px",
  borderRadius: "999px",
  background: "#14B8D4",
  boxShadow: "0 0 0 4px #ECFEFF",
  flexShrink: 0,
};

const statusSummaryStyle: React.CSSProperties = {
  display: "grid",
  gap: "10px",
};

const statusLineStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "11px 12px",
  borderRadius: "12px",
  background: "#f8fafc",
  border: `1px solid ${theme.colors.border}`,
};

const lowStockListStyle: React.CSSProperties = {
  display: "grid",
  gap: "8px",
};

const lowStockRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  gap: "12px",
  padding: "10px 12px",
  borderRadius: "12px",
  border: "1px solid rgba(245, 158, 11, 0.22)",
  background: "rgba(245, 158, 11, 0.07)",
  color: theme.colors.textPrimary,
  textDecoration: "none",
  fontSize: "12px",
};

const lowStockNumbersStyle: React.CSSProperties = {
  display: "grid",
  justifyItems: "end",
  color: theme.colors.textSecondary,
};

export default DashboardPage;
