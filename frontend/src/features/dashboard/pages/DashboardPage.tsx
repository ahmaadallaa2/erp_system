import { useEffect, useState } from "react";
import { theme } from "../../../styles/theme";
import DashboardCard from "../../../components/dashboard-card";
import { listPartners } from "../../partners/api/list-partners";
import { listProducts } from "../../products/api/list-products";
import { listWarehouses } from "../../warehouses/api/list-warehouses";
import { listStockTransactions } from "../../stock-transactions/api/list-stock-transactions";
import { listStockBalances } from "../../stock-balances/api/list-stock-balances";
import { listSalesInvoices } from "../../sales-invoices/api/list-sales-invoices";
import { listPurchaseInvoices } from "../../purchase-invoices/api/list-purchase-invoices";

function DashboardPage() {
  const [partnersCount, setPartnersCount] = useState<string>("...");
  const [productsCount, setProductsCount] = useState<string>("...");
  const [warehousesCount, setWarehousesCount] = useState<string>("...");
  const [stockTransactionsCount, setStockTransactionsCount] = useState<string>("...");
  const [stockBalancesCount, setStockBalancesCount] = useState<string>("...");
  const [salesCount, setSalesCount] = useState<string>("...");
  const [purchasesCount, setPurchasesCount] = useState<string>("...");

  useEffect(() => {
    async function loadStats() {
      try {
        const [
          partners,
          products,
          warehouses,
          stockTransactions,
          stockBalances,
          salesInvoices,
          purchaseInvoices,
        ] = await Promise.all([
          listPartners(),
          listProducts(),
          listWarehouses(),
          listStockTransactions(),
          listStockBalances(),
          listSalesInvoices(),
          listPurchaseInvoices(),
        ]);

        setPartnersCount(partners.length.toString());
        setProductsCount(products.length.toString());
        setWarehousesCount(warehouses.length.toString());
        setStockTransactionsCount(stockTransactions.length.toString());
        setStockBalancesCount(stockBalances.length.toString());
        setSalesCount(salesInvoices.length.toString());
        setPurchasesCount(purchaseInvoices.length.toString());
      } catch (err) {
        console.error("Dashboard error:", err);
        setPartnersCount("--");
        setProductsCount("--");
        setWarehousesCount("--");
        setStockTransactionsCount("--");
        setStockBalancesCount("--");
        setSalesCount("--");
        setPurchasesCount("--");
      }
    }

    loadStats();
  }, []);

  return (
    <main style={pageStyle}>
      <div style={headerStyle}>
        <h1 style={titleStyle}>Dashboard</h1>
        <p style={subtitleStyle}>Overview of your system.</p>
      </div>

      <div style={gridStyle}>
        <DashboardCard
          title="Partners"
          value={partnersCount}
          subtitle="Customers & Suppliers"
        />

        <DashboardCard
          title="Products"
          value={productsCount}
          subtitle="Inventory items"
        />

        <DashboardCard
          title="Warehouses"
          value={warehousesCount}
          subtitle="Storage locations"
        />

        <DashboardCard
          title="Stock Transactions"
          value={stockTransactionsCount}
          subtitle="Inventory documents"
        />

        <DashboardCard
          title="Stock Balances"
          value={stockBalancesCount}
          subtitle="Current stock rows"
        />

        <DashboardCard
          title="Sales"
          value={salesCount}
          subtitle="Sales invoices"
        />

        <DashboardCard
          title="Purchases"
          value={purchasesCount}
          subtitle="Purchase invoices"
        />
      </div>
    </main>
  );
}

const pageStyle: React.CSSProperties = {
  background: theme.colors.background,
  minHeight: "100%",
};

const headerStyle: React.CSSProperties = {
  marginBottom: "24px",
};

const titleStyle: React.CSSProperties = {
  margin: 0,
  color: theme.colors.textPrimary,
};

const subtitleStyle: React.CSSProperties = {
  marginTop: "8px",
  color: theme.colors.textSecondary,
};

const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
  gap: "16px",
};

export default DashboardPage;