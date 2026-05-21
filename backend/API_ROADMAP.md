# API Roadmap - ERP MVP

This document lists the current backend API surface and the roadmap for the next
ERP phases.

## Current Scope

Implemented:

- Authentication and user context.
- Partners, customers, and suppliers.
- Inventory products, units, warehouses, stock transactions, stock movements,
  stock balances, and posting.
- Sales invoices, sales invoice items, and posting.
- Purchase invoices, purchase invoice items, and posting.
- Sales and purchase invoice cancellation with reversing stock/journal entries.
- Accounting account lookup, payments, payment posting, payment cancellation,
  and journal entry detail drill-down.
- Dashboard summary API.
- AI Assistant document APIs.
- OpenAPI schema, Swagger, and ReDoc.

Notes:

- The system is multi-company and partially branch-aware.
- Business logic is implemented in services.
- Posting endpoints execute the irreversible MVP business flow.
- Posted documents are intended to be read-only.
- Reverse/cancel workflows are implemented for posted sales invoices, posted
  purchase invoices, and posted payments. Frontend cancel actions are not yet
  exposed.

## Auth

- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`
- `GET /api/auth/context/`

## Dashboard

- `GET /api/dashboard/summary/`

Returns posted sales, posted purchases, inventory item/quantity summary,
receivable/payable approximation, and low-stock count for the authenticated
user's company.

## Partners

### Partners

- `GET /api/partners/partners/`
- `POST /api/partners/partners/`
- `GET /api/partners/partners/{id}/`
- `PATCH /api/partners/partners/{id}/`

### Partner Lookups

- `GET /api/partners/partners/customers/`
- `GET /api/partners/partners/suppliers/`

## Inventory

### Units

- `GET /api/inventory/units/`
- `POST /api/inventory/units/`
- `GET /api/inventory/units/{id}/`
- `PATCH /api/inventory/units/{id}/`
- `DELETE /api/inventory/units/{id}/`

### Products

- `GET /api/inventory/products/`
- `POST /api/inventory/products/`
- `GET /api/inventory/products/{id}/`
- `PATCH /api/inventory/products/{id}/`
- `DELETE /api/inventory/products/{id}/`

### Warehouses

- `GET /api/inventory/warehouses/`
- `POST /api/inventory/warehouses/`
- `GET /api/inventory/warehouses/{id}/`
- `PATCH /api/inventory/warehouses/{id}/`
- `DELETE /api/inventory/warehouses/{id}/`

### Stock Transactions

- `GET /api/inventory/stock-transactions/`
- `POST /api/inventory/stock-transactions/`
- `GET /api/inventory/stock-transactions/{id}/`
- `PATCH /api/inventory/stock-transactions/{id}/`
- `DELETE /api/inventory/stock-transactions/{id}/`
- `POST /api/inventory/stock-transactions/{id}/post/`

### Stock Movements

- `GET /api/inventory/stock-movements/`
- `POST /api/inventory/stock-movements/`
- `GET /api/inventory/stock-movements/{id}/`
- `PATCH /api/inventory/stock-movements/{id}/`
- `DELETE /api/inventory/stock-movements/{id}/`

### Stock Balances

- `GET /api/inventory/stock-balances/`
- `GET /api/inventory/stock-balances/{id}/`

## Sales

### Sales Invoices

- `GET /api/sales/invoices/`
- `POST /api/sales/invoices/`
- `GET /api/sales/invoices/{id}/`
- `PATCH /api/sales/invoices/{id}/`
- `DELETE /api/sales/invoices/{id}/`
- `POST /api/sales/invoices/{id}/post/`
- `POST /api/sales/invoices/{id}/cancel/`

### Sales Invoice Items

- `GET /api/sales/invoice-items/`
- `POST /api/sales/invoice-items/`
- `GET /api/sales/invoice-items/{id}/`
- `PATCH /api/sales/invoice-items/{id}/`
- `DELETE /api/sales/invoice-items/{id}/`

Posting behavior:

- Reduces stock for non-service products.
- Creates and posts the sales journal entry.
- Debits AR, credits revenue, debits COGS, and credits inventory when stock cost
  exists.
- Sales invoices are credit-only in the MVP.
- Cancellation creates reversing stock and journal entries and marks the invoice
  cancelled.

## Purchases

### Purchase Invoices

- `GET /api/purchases/invoices/`
- `POST /api/purchases/invoices/`
- `GET /api/purchases/invoices/{id}/`
- `PATCH /api/purchases/invoices/{id}/`
- `DELETE /api/purchases/invoices/{id}/`
- `POST /api/purchases/invoices/{id}/post/`
- `POST /api/purchases/invoices/{id}/cancel/`

### Purchase Invoice Items

- `GET /api/purchases/invoice-items/`
- `POST /api/purchases/invoice-items/`
- `GET /api/purchases/invoice-items/{id}/`
- `PATCH /api/purchases/invoice-items/{id}/`
- `DELETE /api/purchases/invoice-items/{id}/`

Posting behavior:

- Increases inventory through an inbound stock transaction.
- Updates weighted average cost.
- Creates and posts the purchase journal entry.
- Debits inventory and credits AP.
- Cancellation creates reversing stock and journal entries and marks the invoice
  cancelled.

## Accounting

### Account Lookup

- `GET /api/accounting/accounts/`
- `GET /api/accounting/accounts/{id}/`

Query parameters:

- `account_type=asset|liability|equity|income|expense`
- `search=<code-or-name>`

Only active, postable accounts for the authenticated user's company are
returned.

### Payments

- `GET /api/accounting/payments/`
- `POST /api/accounting/payments/`
- `GET /api/accounting/payments/{id}/`
- `PATCH /api/accounting/payments/{id}/`
- `DELETE /api/accounting/payments/{id}/`
- `POST /api/accounting/payments/{id}/post/`
- `POST /api/accounting/payments/{id}/cancel/`

Query parameters:

- `status=draft|posted|cancelled`
- `payment_type=inbound|outbound`
- `payment_method=cash|bank`
- `partner=<uuid>`

Posting behavior:

- Inbound payments debit cash/bank and credit AR.
- Outbound payments debit AP and credit cash/bank.
- Payments create and link a posted journal entry.
- Posted payments cannot be updated or deleted.
- Posted payments can be cancelled with a reversing journal entry.
- Payment allocation to specific invoices is not implemented.

### Journal Entries

- `GET /api/accounting/journal-entries/{id}/`

Returns company-scoped journal metadata, totals, and debit/credit line items for
source-document drill-down.

## AI Assistant

Mounted under:

- `/api/ai-assistant/documents/`

The module supports document upload, processing, comparison, deletion, and
question answering. See `backend/apps/ai_assistant/README.md` for module-level
details.

## API Documentation

- `GET /api/schema/`
- `GET /api/docs/`
- `GET /api/redoc/`

## Status Rules

- `draft`: editable and postable.
- `posted`: read-only business state.
- `cancelled`: model state exists, but complete reversal/cancel workflow is not
  implemented for business documents.

## Implemented

- Multi-company company-scoped API behavior.
- Inventory posting and stock balance updates.
- Sales and purchase posting with journal entries.
- Payment posting with cash/bank and AR/AP settlement.
- Payment cancellation with reversing journal entries.
- Sales and purchase cancellation with reversing stock/journal entries.
- Journal entry detail API.
- Chart of accounts seed.
- Dashboard summary endpoint.
- AI Assistant APIs.
- Swagger/ReDoc schema generation.

## In Progress

- Frontend cancel actions.
- Frontend/backend polish around invoice and payment operations.
- Dashboard expansion.

## Known Limitations

- Frontend cancel actions are missing.
- Journal entry detail exists for operational drill-down, but full journal
  browsing UI is missing.
- Permissions are authenticated/company scoped, not complete role-based access.
- Branch scoping limitations remain.
- Inventory valuation is weighted average only.
- Missing payment allocation to invoices.
- Missing accounting and inventory reports.

## Technical Debt

- Some service comments/messages contain encoding issues.
- Error responses are not fully standardized across apps.
- Branch filtering is inconsistent.
- Dashboard values are summary calculations, not ledger reports.
- API test coverage should be broadened for full cross-module workflows.

## Critical Missing Features

- Frontend reversal/cancellation actions.
- Full journal entry list/browse API and UI.
- Invoice-level payment allocation and reconciliation.
- General ledger, trial balance, aged AR/AP, balance sheet, income statement,
  stock card, and inventory valuation reports.
- Role-based permissions.
- Fiscal periods and close/lock behavior.

## Roadmap

### Phase 1: Critical Stabilization

- Add frontend actions for posted sales, purchase, and payment reversal.
- Expand journal drill-down into full journal browsing.
- Make branch scoping explicit and consistent.
- Standardize posted-document immutability and validation errors.
- Expand posting workflow tests.

### Phase 2: Accounting Correctness

- Implement payment allocation to sales/purchase invoices.
- Implement AR/AP reconciliation states.
- Add journal list/detail APIs.
- Add GL and trial balance reports.
- Add fiscal periods and period locks.

### Phase 3: ERP Usability

- Add report endpoints and exports.
- Improve lookup endpoints and filtering.
- Add audit history and approval flows.
- Improve dashboard detail drill-downs.

### Phase 4: Production Hardening

- Add role-based permissions and branch authorization.
- Add observability and structured logging.
- Harden deployment/security settings.
- Add backup/restore runbooks.
- Performance-test high-volume posting and reporting.
