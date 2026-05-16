export const API_ENDPOINTS = {
  auth: {
    login: "/auth/login/",
  },
  dashboard: {
    summary: "/dashboard/summary/",
  },
  partners: {
    list: "/partners/partners/",
    customers: "/partners/partners/customers/",
    suppliers: "/partners/partners/suppliers/",
  },
  inventory: {
    products: "/inventory/products/",
    warehouses: "/inventory/warehouses/",
    stockTransactions: "/inventory/stock-transactions/",
    stockBalances: "/inventory/stock-balances/",
    stockMovements: "/inventory/stock-movements/",
  },
  purchases: {
    invoices: "/purchases/invoices/",
    invoiceItems: "/purchases/invoice-items/",
  },
  sales: {
    invoices: "/sales/invoices/",
    invoiceItems: "/sales/invoice-items/",
  },
  accounting: {
    payments: "/accounting/payments/",
    accounts: "/accounting/accounts/",
    journalEntryDetail: (id: string) => `/accounting/journal-entries/${id}/`,
  },
} as const;
