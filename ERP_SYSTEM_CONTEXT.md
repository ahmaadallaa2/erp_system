# ERP System Context

Master handover document for the `erp_system` repository. This document reflects
the current ERP MVP state after the recent backend and frontend updates.

## Project Overview

The project is a modular Django monolith with a React/Vite frontend. The backend
owns all business rules and exposes REST APIs. The frontend provides an
authenticated operational UI for core ERP workflows.

Current MVP domains:

- Multi-company and branch-aware users.
- Partners for customers and suppliers.
- Inventory products, units, warehouses, stock transactions, stock movements,
  and stock balances.
- Sales invoices.
- Purchase invoices.
- Accounting chart of accounts, journals, journal entries, journal items, and
  payments.
- Dashboard summary API.
- AI Assistant for document upload, processing, retrieval comparison, and
  question answering.

## Repository Structure

```text
erp_system/
  README.md
  ERP_SYSTEM_CONTEXT.md
  backend/
    API_ROADMAP.md
    manage.py
    requirements.txt
    config/
    apps/
      accounting/
      ai_assistant/
      core/
      inventory/
      partners/
      purchases/
      sales/
      users/
  frontend/
    README.md
    package.json
    src/
      App.tsx
      app/
      components/
      features/
      hooks/
      lib/
      pages/
      styles/
```

## Tech Stack

Backend:

- Django 6.
- Django REST Framework.
- PostgreSQL.
- SimpleJWT.
- drf-spectacular for OpenAPI, Swagger, and ReDoc.
- django-cors-headers and django-filter.
- django-unfold for admin UI.
- AI dependencies include pypdf, python-docx, sentence-transformers, FAISS,
  LangChain, LangChain Ollama, and Ollama.

Frontend:

- React 19.
- TypeScript.
- Vite.
- React Router.
- Axios.
- Zustand.
- react-hot-toast.

## Backend Architecture

The backend uses separate Django apps per ERP domain:

- `users`: authentication, JWT endpoints, user context.
- `partners`: partners/customers/suppliers.
- `inventory`: units, products, warehouses, stock transactions, movements,
  balances, and stock posting service.
- `sales`: sales invoices and sales posting service.
- `purchases`: purchase invoices and purchase posting service.
- `accounting`: accounts, journals, entries, journal items, payments, chart of
  accounts seed, and accounting services.
- `core`: dashboard summary API.
- `ai_assistant`: document upload/processing/query module.

Business-critical posting logic lives in services rather than API views:

- `inventory.services.stock_service.StockService`
- `sales.services.sales_service.SalesService`
- `purchases.services.purchase_service.PurchaseService`
- `accounting.services.accounting_service.AccountingService`
- `accounting.services.payment_service.PaymentService`

Most APIs are company scoped through the authenticated user's company. Payments
also require a user branch when created.

## Backend APIs

Mounted API roots:

- `/api/auth/`
- `/api/partners/`
- `/api/inventory/`
- `/api/sales/`
- `/api/purchases/`
- `/api/accounting/`
- `/api/ai-assistant/`
- `/api/dashboard/summary/`
- `/api/schema/`, `/api/docs/`, `/api/redoc/`

Key endpoints:

- Auth: `POST /api/auth/login/`, `POST /api/auth/refresh/`,
  `GET /api/auth/me/`, `GET /api/auth/context/`.
- Partners: `/api/partners/partners/`, `/customers/`, `/suppliers/`.
- Inventory: `/units/`, `/products/`, `/warehouses/`,
  `/stock-transactions/`, `/stock-transactions/{id}/post/`,
  `/stock-movements/`, `/stock-balances/`.
- Sales: `/api/sales/invoices/`, `/api/sales/invoice-items/`,
  `/api/sales/invoices/{id}/post/`, `/api/sales/invoices/{id}/cancel/`.
- Purchases: `/api/purchases/invoices/`,
  `/api/purchases/invoice-items/`, `/api/purchases/invoices/{id}/post/`,
  `/api/purchases/invoices/{id}/cancel/`.
- Accounting: `/api/accounting/accounts/`, `/api/accounting/payments/`,
  `/api/accounting/payments/{id}/post/`,
  `/api/accounting/payments/{id}/cancel/`,
  `/api/accounting/journal-entries/{id}/`.
- AI Assistant: document CRUD/processing/query endpoints under
  `/api/ai-assistant/documents/`.

## Multi-Company and Branch Model

The MVP is multi-company. Core documents and master data are associated with a
company. User-specific queries generally filter by `request.user.company`.

Branch support exists on users and payments, and documents have branch-aware
foundations in the domain model. Current branch enforcement is incomplete: some
list and dashboard surfaces are company scoped only, not strict branch scoped.
This should be treated as a known limitation before production use.

## Inventory Workflow

Inventory supports:

- Products, units, categories, warehouses.
- Stock transactions with `IN`, `OUT`, and `TRANSFER` types.
- Stock movements under a draft stock transaction.
- Posting stock transactions to update stock balances.
- Insufficient-stock validation for outbound and transfer transactions.
- Weighted average cost updates when inbound stock is posted.
- Service products are excluded from physical stock movement in sales posting.

Current inventory valuation is MVP-level weighted average cost. It does not yet
include valuation layers, period close, landed cost allocation, inventory
adjustment approvals, or inventory valuation reports.

## Sales Workflow

Sales invoice behavior:

- Create draft sales invoice.
- Add invoice items while draft.
- Post invoice.
- Posting validates draft status, non-empty items, and positive total.
- For stock products, posting creates an `OUT` stock transaction and reduces
  stock through `StockService`.
- Service items do not create stock movement.
- Posting creates a sales journal entry and links it to the invoice.
- Posted invoices are treated as read-only by service/API/admin behavior.
- Posted invoices can be cancelled through the backend/API/admin. Cancellation
  creates a reversing journal entry and restores stock for stock products through
  an inbound reversal stock transaction.

Current invoice behavior:

- Frontend supports list, create draft, details, add items, and post.
- Details page links to the journal entry drill-down when a journal entry exists.
- Sales invoices are credit-only in the MVP. No immediate cash sale, mixed
  payment, invoice payment terms, or allocation workflow exists yet.

## Purchase Workflow

Purchase invoice behavior:

- Create draft purchase invoice.
- Add invoice items while draft.
- Post invoice.
- Posting validates draft status and non-empty items.
- Posting creates an `IN` stock transaction, stock movements, and updates stock
  balances.
- Inbound stock updates product weighted average cost.
- Posting creates a purchase journal entry and links it to the invoice.
- Posted invoices are treated as read-only by service/API/admin behavior.
- Posted invoices can be cancelled through the backend/API/admin. Cancellation
  creates a reversing journal entry and removes stock through an outbound
  reversal stock transaction.

Purchase costing currently posts the invoice total to inventory. Advanced landed
cost allocation and separate purchase expense treatment are not complete.

## Payment Workflow

Payment behavior:

- Create draft payment.
- Payment type is `inbound` or `outbound`.
- Payment method is `cash` or `bank`.
- User selects a postable asset account for cash/bank.
- Post draft payment.
- Posting creates and links a journal entry, then marks the payment `posted`.
- Posted payments cannot be updated or deleted through the API.
- Outbound payments validate available balance on the selected cash/bank account.
- Posted payments can be cancelled through the backend/API/admin. Cancellation
  creates a reversing journal entry and marks the payment cancelled.

Accounting effect:

- Inbound: debit selected cash/bank asset account, credit Accounts Receivable
  (`1003`) for the customer/partner.
- Outbound: debit Accounts Payable (`2001`) for the supplier/partner, credit
  selected cash/bank asset account.

Known payment limitation:

- Payments settle AR/AP at partner-account level only. There is no allocation to
  specific sales or purchase invoices, no partial allocation table, and no
  unapplied cash workflow.

## Accounting Workflow

Implemented accounting objects:

- `Account`
- `Journal`
- `JournalEntry`
- `JournalItem`
- `Payment`

Implemented chart of accounts seed:

- `1000` Assets, non-postable.
- `1001` Bank, asset, postable.
- `1002` Cash, asset, postable.
- `1003` Accounts Receivable, asset, postable, reconciliation-enabled.
- `1004` Inventory, asset, postable.
- `2000` Liabilities, non-postable.
- `2001` Accounts Payable, liability, postable, reconciliation-enabled.
- `3000` Equity, non-postable.
- `3001` Owner Capital, equity, postable.
- `4000` Income, non-postable.
- `4001` Sales Revenue, income, postable.
- `5000` Expenses, non-postable.
- `5001` Cost of Goods Sold, expense, postable.
- `5002` Operating Expenses, expense, postable.
- `5003` Purchase Expenses, expense, postable.

Sales accounting behavior:

- Posting creates a sales journal (`SAL`) if needed.
- Debits Accounts Receivable (`1003`) with partner set to the customer.
- Credits Sales Revenue (`4001`).
- Calculates COGS from stock item quantity times product average cost.
- If COGS is greater than zero, debits Cost of Goods Sold (`5001`) and credits
  Inventory (`1004`).
- Posts the journal entry and links it to the invoice.

Purchase accounting behavior:

- Posting creates a purchase journal (`PUR`) if needed.
- Debits Inventory (`1004`) for invoice total.
- Credits Accounts Payable (`2001`) with partner set to the supplier.
- Posts the journal entry and links it to the invoice.

Payment accounting behavior:

- Posting creates a cash (`CSH`) or bank (`BNK`) journal if needed.
- Inbound payments debit selected cash/bank account and credit AR.
- Outbound payments debit AP and credit selected cash/bank account.
- Posts the journal entry and links it to the payment.

Accounting safeguards:

- Duplicate journal creation for the same invoice reference/journal is guarded.
- Posted/cancelled journal entries are protected from direct mutation.
- Journal items must balance by entry posting rules.
- Non-postable accounts cannot be used for journal items or payment cash/bank
  account selection.
- Admin hardening prevents direct changes/deletes to posted or cancelled sales
  invoices, purchase invoices, payments, journal entries, stock transactions, and
  their protected line/inlines.
- Journal entry detail API exposes journal metadata and debit/credit lines for
  source-document drill-down.

## Dashboard API

`GET /api/dashboard/summary/` returns company-level summary values:

- `total_sales`: posted sales invoice total.
- `total_purchases`: posted purchase invoice total.
- `inventory_items`: distinct products with stock balances.
- `inventory_quantity`: total stock balance quantity.
- `customers_receivable`: posted sales minus posted inbound payments.
- `suppliers_payable`: posted purchases minus posted outbound payments.
- `low_stock_products`: count of stock balances at or below reorder point.

This is a summary endpoint, not a full reporting engine.

## AI Assistant Module

The AI Assistant module is implemented separately from ERP accounting workflows.
It supports document upload, document processing, retrieval comparison, document
deletion, and question answering against processed content.

See `backend/apps/ai_assistant/README.md` for module-specific details and test
assets.

## Frontend Architecture

The frontend is a Vite React app with feature folders under `frontend/src`.

Key structure:

- `App.tsx`: route definitions.
- `app/layouts/AppLayout.tsx`: authenticated shell.
- `app/routes/ProtectedRoute.tsx`: route guard.
- `app/store/auth-store.ts`: auth token/user state.
- `hooks/useAutoLogout.ts`: inactivity logout.
- `lib/api/axios.ts`: Axios client.
- `lib/api/endpoints.ts`: API endpoint constants.
- `components/ui/mvp.tsx`: shared MVP UI primitives.
- `features/*`: feature pages, API wrappers, and types.

Implemented routes:

- `/login`
- `/` redirects to `/dashboard`
- `/dashboard`
- `/partners`
- `/products`
- `/warehouses`
- `/stock-transactions`
- `/stock-balances`
- `/stock-movements`
- `/product-movements`
- `/warehouse-balances`
- `/purchase-invoices`
- `/purchase-invoices/new`
- `/purchase-invoices/:id`
- `/sales-invoices`
- `/sales-invoices/new`
- `/sales-invoices/:id`
- `/payments`
- `/general-ledger`
- `/accounting/journal-entries/:id`
- `/ai-assistant`

Shared UI components:

- `PageHeader`
- `StatusBadge`
- `LoadingState`
- `ErrorMessage`
- `EmptyState`
- `SectionCard`
- `MetricCard`
- `ComparisonBar`
- `ProgressBar`

Auto logout:

- `useAutoLogout` runs inside `AppLayout`.
- Authenticated users are logged out after 30 minutes of inactivity.
- Activity events reset the timer: mouse movement, keydown, click, scroll, and
  touch start.
- Timeout clears auth state, navigates to `/login`, and shows a toast.

## Frontend Feature Notes

Dashboard:

- Calls `/api/dashboard/summary/`.
- Displays posted sales, posted purchases, inventory quantity/items,
  receivable/payable summaries, and low-stock count.

Payments UI:

- Lists payments.
- Creates draft payments.
- Supports inbound customer receipt and outbound supplier payment modes.
- Supports cash/bank payment method.
- Loads postable accounts from `/api/accounting/accounts/`.
- Posts draft payments through `/api/accounting/payments/{id}/post/`.
- Shows linked journal entries for drill-down.
- Does not expose cancel buttons yet.
- Does not allocate payments to invoices.

Invoice UI:

- Sales and purchase invoice pages support list, create draft, detail, add item,
  and post.
- Posted invoice detail pages no longer allow adding items.
- Detail pages link to the journal entry drill-down when a journal entry exists.
- There is no frontend reversal action.
- Sales UI explicitly notes the credit-only MVP limitation.

## Implemented

- Multi-company ERP foundation.
- Authenticated REST API.
- Partners/customers/suppliers.
- Inventory products, warehouses, stock transactions, stock balances, stock
  movements, posting, and average cost update.
- Sales invoice posting with stock reduction and full sales accounting entry.
- Purchase invoice posting with inventory increase and AP accounting entry.
- Sales and purchase invoice cancellation with reversing stock/journal entries.
- Chart of accounts seed.
- Journal, journal entry, and journal item models.
- Payment model, payment API, and payment posting.
- Payment cancellation with reversing journal entries.
- Journal entry detail API and frontend drill-down.
- Admin hardening for posted/cancelled documents and accounting records.
- Dashboard summary API and frontend.
- Frontend routes for dashboard, master data, inventory inquiry, invoices,
  payments, and AI Assistant.
- Auto logout frontend behavior.
- AI Assistant document workflow.

## In Progress

- Frontend cancel actions for sales, purchases, and payments.
- Operational UX for payments and invoices.
- Dashboard as a lightweight executive summary.
- Stabilizing accounting defaults and standard chart of accounts.

## Known Limitations

- Backend/API/admin reversal exists for posted sales invoices, purchase invoices,
  and payments; frontend cancel actions are not exposed yet.
- Journal entry drill-down exists, but there is no full journal browser UI.
- Permissions are not yet full role/permission based.
- Branch scoping is incomplete.
- Inventory valuation is weighted-average only and lacks production-grade audit
  depth.
- Payment allocation to invoices is missing.
- Reports are missing beyond the dashboard summary.
- Sales are credit-only in the MVP.
- No production-ready fiscal period closing.
- No tax/VAT engine.
- No multi-currency.
- No formal approval workflow.

## Technical Debt

- Some source comments/messages contain mojibake and should be normalized.
- Frontend styling is mostly inline and MVP-oriented.
- API behavior is covered by focused tests, but end-to-end workflow tests are
  still limited.
- Accounting APIs expose account lookup, payments, journal entry detail, and a
  general ledger report, but not complete journal browsing/reporting.
- Dashboard receivable/payable values are summary approximations based on
  posted totals minus posted payments, not ledger-aged reports.
- Branch filtering should be made consistent across APIs.
- Error handling and validation messages should be standardized.

## Critical Missing Features

- Frontend reversal/cancellation actions.
- Full journal entry browser beyond source-document drill-down.
- Payment allocation/reconciliation against specific invoices.
- Aged receivables and aged payables reports.
- General ledger, trial balance, balance sheet, income statement.
- Inventory valuation and stock card reports.
- Role-based permissions and branch-level authorization.
- Audit trail suitable for production finance operations.
- Period close and posted-period lock.

## Roadmap

### Phase 1: Critical Stabilization

- Add frontend reversal actions for sales, purchases, and payments.
- Expand journal drill-down into a full journal browser.
- Standardize posted-document immutability and error responses.
- Complete branch scoping rules for list/detail/dashboard surfaces.
- Expand workflow tests for sales, purchases, payments, and inventory posting.

### Phase 2: Accounting Correctness

- Add payment allocation to invoices.
- Add AR/AP reconciliation states and unapplied payment handling.
- Add journal listing/detail APIs and frontend viewer.
- Add general ledger and trial balance reports.
- Add fiscal periods, period close, and posted-period locks.
- Review purchase costing and landed cost behavior.

### Phase 3: ERP Usability

- Improve invoice/payment forms and lookup ergonomics.
- Add reports for aged receivables, aged payables, inventory valuation, stock
  card, income statement, and balance sheet.
- Add search/filter/export flows across operational lists.
- Add user-facing audit history.
- Add approval flows for high-risk transactions.

### Phase 4: Production Hardening

- Implement role-based permissions and branch authorization.
- Add comprehensive API and E2E test coverage.
- Add observability, structured logging, and operational monitoring.
- Harden deployment configuration, secrets, CORS, and security headers.
- Add backup/restore and data migration runbooks.
- Performance-test dashboard, reports, and high-volume posting workflows.

## Summary for Next Assistant

Treat the system as an ERP MVP with real posting workflows, not just CRUD.
Sales, purchases, inventory, payments, accounting, dashboard, and AI Assistant
are all implemented at MVP level. Backend/API/admin reversal exists for sales,
purchases, and payments, and journal drill-down exists. The biggest functional
gaps are frontend reversal actions, payment allocation, broader reports,
permissions, branch scoping, and production-grade accounting controls.
