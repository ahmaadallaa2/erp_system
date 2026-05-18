import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router";
import {
  ComparisonBar,
  EmptyStateCard,
  ErrorMessage,
  LoadingState,
  MetricCard,
  PageHeader,
  ProgressBar,
  SectionCard,
  formatNumber,
} from "../../../components/ui/mvp";
import { theme } from "../../../styles/theme";
import { getDashboardSummary } from "../api/dashboard-api";
import type { DashboardSummary } from "../api/dashboard-api";

function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      setIsLoading(true);
      setError(null);

      try {
        const data = await getDashboardSummary();
        setSummary(data);
      } catch (err) {
        console.error("Dashboard error:", err);
        setError("تعذر تحميل ملخص لوحة التحكم.");
      } finally {
        setIsLoading(false);
      }
    }

    loadStats();
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

  return (
    <main style={pageStyle}>
      <div style={breadcrumbStyle}>
        <strong>لوحة التحكم</strong>
        <span>/</span>
        <span>النظام</span>
      </div>

      <PageHeader title="لوحة التحكم" subtitle="متابعة عمليات الشركة ومؤشرات النشاط الرئيسية" />

      <ErrorMessage message={error || ""} />
      {isLoading && <LoadingState label="جاري تحميل ملخص لوحة التحكم..." />}

      {!isLoading && !error && (
        <div style={dashboardStackStyle}>
          <section style={dashboardGridStyle}>
            <DashboardGridItem span={3}>
              <MetricCard
              title="إجمالي المبيعات"
              value={formatNumber(metrics.totalSales)}
              subtitle="فواتير المبيعات المرحلة"
              tone="info"
              accentColor="#14B8D4"
              />
            </DashboardGridItem>
            <DashboardGridItem span={3}>
              <MetricCard
              title="إجمالي المشتريات"
              value={formatNumber(metrics.totalPurchases)}
              subtitle="فواتير المشتريات المرحلة"
              tone="success"
              accentColor="#10B981"
              />
            </DashboardGridItem>
            <DashboardGridItem span={3}>
              <MetricCard
              title="كمية المخزون"
              value={formatNumber(metrics.inventoryQuantity)}
              subtitle={`${formatNumber(metrics.inventoryItems)} عناصر مخزنية`}
              tone="neutral"
              accentColor="#6366F1"
              />
            </DashboardGridItem>
            <DashboardGridItem span={3}>
              <MetricCard
              title="مستحقات العملاء"
              value={formatNumber(metrics.receivables)}
              subtitle="رصيد العملاء المفتوح"
              tone="warning"
              accentColor="#F59E0B"
              />
            </DashboardGridItem>
          </section>

          <section style={dashboardGridStyle}>
            <DashboardGridItem span={4}>
              <SectionCard title="النشاط الأخير" subtitle="آخر الحركات والتحديثات">
                <EmptyStateCard title="البيانات غير متوفرة حالياً" message="سجل النشاط غير متاح في هذه النسخة." />
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="حالة المخزون" subtitle="مستويات المخزون الحالية عبر المخازن">
                <div style={inventoryHealthStyle}>
                  <ProgressBar
                    label="عناصر أعلى من حد إعادة الطلب"
                    value={Math.max(metrics.inventoryItems - metrics.lowStockProducts, 0)}
                    max={Math.max(metrics.inventoryItems, 1)}
                    tone="success"
                  />
                  <ProgressBar
                    label="نسبة المخزون المنخفض"
                    value={metrics.lowStockProducts}
                    max={Math.max(metrics.inventoryItems, 1)}
                    tone={metrics.lowStockProducts > 0 ? "warning" : "success"}
                  />
                </div>
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="إجمالي المبيعات" subtitle="نظرة عامة على مؤشرات الإيرادات">
                <ComparisonBar
                  label="المبيعات مقابل المشتريات"
                  leftLabel="المبيعات"
                  leftValue={metrics.totalSales}
                  rightLabel="المشتريات"
                  rightValue={metrics.totalPurchases}
                />
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="إجراءات سريعة" subtitle="العمليات الأكثر استخداماً">
                <div style={quickActionsGridStyle}>
                  <QuickAction to="/sales-invoices" label="فواتير المبيعات" />
                  <QuickAction to="/purchase-invoices" label="فواتير المشتريات" />
                  <QuickAction to="/payments" label="المدفوعات" />
                  <QuickAction to="/stock-transactions" label="حركات المخزون" />
                </div>
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="المدفوعات المعلقة" subtitle="الفواتير والمدفوعات المستحقة">
                <div style={paymentSummaryStyle}>
                  <MetricMini label="مستحقات العملاء" value={metrics.receivables} />
                  <MetricMini label="مستحقات الموردين" value={metrics.payables} />
                </div>
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={4}>
              <SectionCard title="نظرة على المبيعات" subtitle="متابعة أداء المبيعات">
                <EmptyStateCard
                  title="البيانات غير متوفرة حالياً"
                  message="تحليلات المبيعات التفصيلية تحتاج إلى نقطة تقارير لاحقة."
                />
              </SectionCard>
            </DashboardGridItem>
          </section>

          <section style={dashboardGridStyle}>
            <DashboardGridItem span={6}>
              <SectionCard title="تنبيهات المخزون المنخفض" subtitle="منتجات عند حد إعادة الطلب أو أقل">
                <div style={alertCardStyle(metrics.lowStockProducts > 0)}>
                  <div style={alertNumberStyle}>{formatNumber(metrics.lowStockProducts)}</div>
                  <div>
                    <strong>
                      {metrics.lowStockProducts > 0
                        ? "منتجات تحتاج إلى متابعة"
                        : "لا توجد منتجات منخفضة المخزون"}
                    </strong>
                    <p style={alertTextStyle}>هذه القيمة من ملخص لوحة التحكم الحالي.</p>
                  </div>
                </div>
              </SectionCard>
            </DashboardGridItem>

            <DashboardGridItem span={6}>
              <SectionCard title="تحليلات" subtitle="مساحة رسمية للتقارير غير المتاحة">
                <div style={placeholderGridStyle}>
                  <EmptyStateCard title="البيانات غير متوفرة حالياً" message="تقرير هامش الربح غير متاح حالياً." />
                  <EmptyStateCard title="البيانات غير متوفرة حالياً" message="تقرير التحصيل اليومي غير متاح حالياً." />
                </div>
              </SectionCard>
            </DashboardGridItem>
          </section>
        </div>
      )}
    </main>
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
  justifyContent: "flex-start",
  gap: "8px",
  marginBottom: "4px",
  color: "#64748b",
  fontSize: "12px",
};

const dashboardStackStyle: React.CSSProperties = {
  display: "grid",
  gap: "18px",
};

const dashboardGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(12, minmax(0, 1fr))",
  gap: "18px",
};

const inventoryHealthStyle: React.CSSProperties = {
  minHeight: "108px",
  display: "grid",
  alignContent: "center",
  gap: "14px",
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

const paymentSummaryStyle: React.CSSProperties = {
  minHeight: "108px",
  display: "grid",
  gap: "10px",
  alignContent: "center",
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

function alertCardStyle(hasAlert: boolean): React.CSSProperties {
  return {
    minHeight: "108px",
    display: "flex",
    alignItems: "center",
    gap: "14px",
    padding: "16px",
    borderRadius: "12px",
    border: `1px solid ${hasAlert ? "rgba(245, 158, 11, 0.28)" : "rgba(20, 184, 212, 0.24)"}`,
    background: hasAlert ? "rgba(245, 158, 11, 0.08)" : "#ECFEFF",
  };
}

const alertNumberStyle: React.CSSProperties = {
  width: "52px",
  height: "52px",
  borderRadius: "14px",
  background: "#ffffff",
  border: `1px solid ${theme.colors.border}`,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  color: "#020617",
  fontSize: "22px",
  fontWeight: 900,
  flexShrink: 0,
};

const alertTextStyle: React.CSSProperties = {
  margin: "6px 0 0",
  color: "#64748b",
  fontSize: "13px",
  lineHeight: 1.6,
};

const placeholderGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: "10px",
};

export default DashboardPage;
