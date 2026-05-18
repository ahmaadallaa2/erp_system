import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import AppLayout from "./app/layouts/AppLayout";
import ProtectedRoute from "./app/routes/ProtectedRoute";
import DashboardPage from "./features/dashboard/pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import PartnersPage from "./features/partners/pages/PartnersPage";
import ProductsPage from "./features/products/pages/ProductsPage";
import WarehousesPage from "./features/warehouses/pages/WarehousesPage";
import StockTransactionsPage from "./features/stock-transactions/pages/StockTransactionsPage";
import StockBalancesPage from "./features/stock-balances/pages/StockBalancesPage";
import StockMovementsPage from "./features/stock-movements/pages/StockMovementsPage";
import ProductMovementHistoryPage from "./features/inventory/pages/ProductMovementHistoryPage";
import WarehouseBalancesReportPage from "./features/inventory/pages/WarehouseBalancesReportPage";
import PurchaseInvoicesPage from "./features/purchase-invoices/pages/PurchaseInvoicesPage";
import CreatePurchaseInvoicePage from "./features/purchase-invoices/pages/CreatePurchaseInvoicePage";
import PurchaseInvoiceDetailsPage from "./features/purchase-invoices/pages/PurchaseInvoiceDetailsPage";
import SalesInvoicesPage from "./features/sales-invoices/pages/SalesInvoicesPage";
import CreateSalesInvoicePage from "./features/sales-invoices/pages/CreateSalesInvoicePage";
import SalesInvoiceDetailsPage from "./features/sales-invoices/pages/SalesInvoiceDetailsPage";
import AiAssistantPage from "./features/ai-assistant/pages/AiAssistantPage";
import PaymentsPage from "./features/payments/pages/PaymentsPage";
import JournalEntryDetailPage from "./features/accounting/pages/JournalEntryDetailPage";
import GeneralLedgerPage from "./features/accounting/pages/GeneralLedgerPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/partners" element={<PartnersPage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/warehouses" element={<WarehousesPage />} />
            <Route path="/stock-transactions" element={<StockTransactionsPage />} />
            <Route path="/stock-balances" element={<StockBalancesPage />} />
            <Route path="/stock-movements" element={<StockMovementsPage />} />
            <Route path="/product-movements" element={<ProductMovementHistoryPage />} />
            <Route path="/warehouse-balances" element={<WarehouseBalancesReportPage />} />
            <Route path="/purchase-invoices" element={<PurchaseInvoicesPage />} />
            <Route path="/purchase-invoices/new" element={<CreatePurchaseInvoicePage />} />
            <Route path="/purchase-invoices/:id" element={<PurchaseInvoiceDetailsPage />} />
            <Route path="/sales-invoices" element={<SalesInvoicesPage />} />
            <Route path="/sales-invoices/new" element={<CreateSalesInvoicePage />} />
            <Route path="/sales-invoices/:id" element={<SalesInvoiceDetailsPage />} />
            <Route path="/payments" element={<PaymentsPage />} />
            <Route path="/general-ledger" element={<GeneralLedgerPage />} />
            <Route path="/accounting/journal-entries/:id" element={<JournalEntryDetailPage />} />
            <Route path="/ai-assistant" element={<AiAssistantPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
