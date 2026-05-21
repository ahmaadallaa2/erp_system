# ERP Frontend

React + TypeScript + Vite frontend for the ERP MVP.

## Current Routes

Public:

- `/login`

Protected:

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

## Current Feature Coverage

Implemented:

- Login and protected route handling.
- Authenticated layout with navbar, sidebar, footer, and main content outlet.
- Dashboard summary page.
- Partners page.
- Products page.
- Warehouses page.
- Stock transactions, stock balances, and stock movements pages.
- Purchase invoice list/create/detail/post flow.
- Sales invoice list/create/detail/post flow.
- Payments list/create/post flow.
- General ledger report page.
- Journal entry drill-down page from posted invoices and payments.
- AI Assistant page.
- Shared MVP UI primitives.
- Auto logout after 30 minutes of inactivity.

## Dashboard

The dashboard calls:

- `/api/dashboard/summary/`

It displays:

- Posted sales total.
- Posted purchase total.
- Inventory item count.
- Inventory quantity.
- Customers receivable summary.
- Suppliers payable summary.
- Low-stock product count.

These values are summary calculations from operational tables. They are not a
replacement for ledger reports.

## Payments UI

The payments page supports:

- Listing payments.
- Creating draft payments.
- Inbound customer receipts.
- Outbound supplier payments.
- Cash or bank payment method.
- Selecting an active postable account from `/api/accounting/accounts/`.
- Posting draft payments through `/api/accounting/payments/{id}/post/`.
- Opening linked journal entry detail pages.
- Summary cards for received, paid, and draft payment counts.

Current limitation:

- Payments are not allocated to specific invoices. Posting settles AR/AP at
  partner-account level only.
- Cancel buttons are not exposed in the frontend yet.

## Invoice UI

Sales invoices:

- List invoices.
- Create draft invoice.
- View details.
- Add line items while draft.
- Post draft invoice.
- Link to journal entry drill-down when a journal entry exists.
- Explicitly note that sales invoices are credit-only in the MVP.

Purchase invoices:

- List invoices.
- Create draft invoice.
- View details.
- Add line items while draft.
- Post draft invoice.
- Link to journal entry drill-down when a journal entry exists.

Current invoice limitations:

- No frontend reverse/cancel action.
- Journal entry drill-down exists, but there is no full journal browser UI.
- No payment allocation view.
- No cash-sale mode for sales invoices.

## Auto Logout

`useAutoLogout` is mounted in `AppLayout`.

Behavior:

- Starts only when the user is authenticated.
- Logs the user out after 30 minutes of inactivity.
- Resets the timer on mouse movement, keydown, click, scroll, and touch start.
- Clears auth state, navigates to `/login`, and shows a toast message.

## Shared UI Components

Shared MVP components live in `src/components/ui/mvp.tsx`:

- `PageHeader`
- `StatusBadge`
- `LoadingState`
- `ErrorMessage`
- `EmptyState`
- `SectionCard`
- `MetricCard`
- `ComparisonBar`
- `ProgressBar`

Layout components:

- `src/components/layout/navbar.tsx`
- `src/components/layout/sidebar.tsx`
- `src/components/layout/footer.tsx`
- `src/app/layouts/AppLayout.tsx`

## API Client

Endpoint constants are in:

- `src/lib/api/endpoints.ts`

Axios client code is in:

- `src/lib/api/axios.ts`

The frontend currently consumes these API groups:

- Auth.
- Dashboard.
- Partners.
- Inventory.
- Purchases.
- Sales.
- Accounting payments/accounts.
- AI Assistant feature APIs.

## Implemented

- Authenticated ERP shell.
- Core operational route set.
- Dashboard.
- Inventory inquiry pages.
- Sales and purchase invoice workflows.
- Payments UI.
- General ledger report.
- Journal entry drill-down.
- AI Assistant page.
- Auto logout.
- Shared UI primitives.

## In Progress

- Frontend cancel actions for sales invoices, purchase invoices, and payments.
- Dashboard and payment UX refinement.
- Better operational filtering/search.

## Known Limitations

- Frontend reverse/cancel actions are missing.
- Journal entry drill-down exists, but full journal browsing is missing.
- Permissions UI is not role-aware.
- Branch scoping is not visible or consistently enforced in the UI.
- Inventory valuation reports are missing.
- Payment allocation is missing.
- Reports are missing beyond dashboard summary.
- Sales invoices are credit-only in the MVP.

## Technical Debt

- Styling is inline and MVP-oriented.
- Some pages use basic tables and local state rather than a shared data-grid or
  query cache.
- Error handling is improving but not fully standardized.
- No full E2E coverage for frontend workflows yet.

## Critical Missing Features

- Full journal browsing pages beyond source-document drill-down.
- Invoice payment allocation UI.
- Reversal/cancellation UI.
- Accounting reports.
- Inventory valuation and stock card reports.
- Role-based navigation and permissions.

## Roadmap

### Phase 1: Critical Stabilization

- Add UI for reversal/cancel workflows when backend support exists.
- Add journal drill-down from invoices and payments.
- Make branch/company context visible.
- Standardize form validation and API error display.

### Phase 2: Accounting Correctness

- Add payment allocation UI.
- Add journal entry list/detail pages.
- Add GL, trial balance, and AR/AP aging views.

### Phase 3: ERP Usability

- Add richer filters, search, pagination, and export flows.
- Improve invoice and payment forms.
- Add report navigation and drill-downs.
- Add audit/approval UX.

### Phase 4: Production Hardening

- Add role-aware navigation and permission handling.
- Add frontend E2E tests.
- Add observability-friendly error boundaries.
- Harden production build/runtime configuration.

## Development

```powershell
npm install
npm run dev
```
