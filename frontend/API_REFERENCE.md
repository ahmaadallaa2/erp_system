# Wethaq ERP — Backend API Reference

Reference for the React frontend. Generated from the backend's OpenAPI schema
(`python manage.py spectacular`) and checked against the view, serializer and
permission code. The interactive version is at `/api/docs/` (Swagger) and
`/api/redoc/` — public when `DEBUG=True`, staff-only (`is_staff`) in production.

## Contents

- [Conventions](#conventions)
- [Roles and permissions](#roles-and-permissions)
- [Auth and Users](#auth-and-users)
- [Core (Dashboard)](#core-dashboard)
- [Partners](#partners)
- [Inventory](#inventory)
- [Sales](#sales)
- [Purchases](#purchases)
- [Accounting](#accounting)
- [AI Assistant](#ai-assistant)
- [System endpoints](#system-endpoints)

---

## Conventions

| Topic | Rule |
| --- | --- |
| Base URL | `http://127.0.0.1:9000/api` locally (see `src/lib/api/axios.ts`). All paths below are relative to the host and end with `/`. |
| Auth header | `Authorization: Bearer <access>` on every endpoint except login and refresh. |
| Tokens | Access token lives 60 minutes, refresh token 7 days. Login and refresh are rate limited per IP (default `10/minute`, HTTP 429). |
| Content type | `application/json`, except AI document upload (`multipart/form-data`). |
| IDs | Every primary key and foreign key is a UUID string. |
| Money / quantities | Decimal values are sent and returned as **strings**, e.g. `"1250.00"`. Send strings (or numbers) and never do float math on them. |
| Dates | `date` = `YYYY-MM-DD`; `date-time` = ISO 8601 with timezone (UTC). |
| Lists | Not paginated: list endpoints return a plain JSON array. |
| Company scoping | Every query is limited to the signed-in user's company; objects of other companies return 404. Users without a company get 403 on business endpoints. |
| Branch scoping | Users with company-wide access (superuser, `system_admin`/`company_admin` user types, or the CompanyAdmin, AccountingManager, Auditor roles) see all branches. Everyone else only sees documents of their own branch. Documents are created in the user's branch. |
| Read-only fields | Fields marked *(read-only)* below are returned but ignored if sent. |

### Document lifecycle

Sales invoices, purchase invoices, payments and stock transactions share one lifecycle:

`draft` → **post** → `posted` → **cancel** → `cancelled`

- Only `draft` documents can be edited or deleted, and only draft documents accept new line items.
- Posting creates the stock movements and/or journal entry and is irreversible; cancelling a posted document creates reversing entries.
- Deletes of master data and documents are soft deletes (the record is hidden, not removed).

### Errors

| Status | Body |
| --- | --- |
| 400 Validation | `{"field_name": ["message", ...]}` or `{"non_field_errors": ["message"]}`. Business-rule errors from services use the same shape (often `non_field_errors` or a `detail` string). |
| 401 | `{"detail": "Authentication credentials were not provided."}` or an invalid/expired token message. Refresh the token and retry once; on failure send the user to login. |
| 403 | `{"detail": "..."}` — missing role, wrong branch, or no company. |
| 404 | `{"detail": "No ... matches the given query."}` — also returned for other companies' objects. |
| 429 | `{"detail": "Request was throttled. Expected available in N seconds."}` (login / refresh). |

---

## Roles and permissions

Users have one `user_type` and any number of ERP **roles** (Django groups).

| `user_type` | Meaning |
| --- | --- |
| `system_admin` | Platform administrator. Same as a superuser for the API: all companies, all actions. |
| `company_admin` | Administrator of one company. Always gets the CompanyAdmin role. |
| `branch_manager` | Manager of one branch. Always gets the BranchManager role. |
| `employee` | Regular user; access comes from roles. |

Roles: `CompanyAdmin`, `BranchManager`, `SalesUser`, `SalesManager`, `PurchaseUser`, `PurchaseManager`, `InventoryUser`, `InventoryManager`, `Accountant`, `AccountingManager`, `Auditor`, `AIUser`, `AIAdmin`.

**Base rule:** any authenticated user that belongs to a company can list, read, create, update and delete (draft) records of their company and branch. The following actions additionally require a role. Superusers and the `system_admin` / `company_admin` user types pass every role check.

| Action | Endpoint | Allowed roles |
| --- | --- | --- |
| Post sales invoice | `POST /api/sales/invoices/{id}/post/` | CompanyAdmin, SalesManager |
| Cancel sales invoice | `POST /api/sales/invoices/{id}/cancel/` | CompanyAdmin, SalesManager, AccountingManager |
| Post purchase invoice | `POST /api/purchases/invoices/{id}/post/` | CompanyAdmin, PurchaseManager |
| Cancel purchase invoice | `POST /api/purchases/invoices/{id}/cancel/` | CompanyAdmin, PurchaseManager, AccountingManager |
| Post stock transaction | `POST /api/inventory/stock-transactions/{id}/post/` | CompanyAdmin, InventoryManager |
| Post payment | `POST /api/accounting/payments/{id}/post/` | CompanyAdmin, Accountant, AccountingManager |
| Cancel payment | `POST /api/accounting/payments/{id}/cancel/` | CompanyAdmin, AccountingManager |
| Allocate payment | `POST /api/accounting/payments/{id}/allocate/` | CompanyAdmin, Accountant, AccountingManager |
| Accounting reports | `GET /api/accounting/reports/*` | CompanyAdmin, Accountant, AccountingManager, Auditor |
| User administration | `/api/auth/users/` | `system_admin` / superuser (all users) or company admin (`company_admin` type or CompanyAdmin role; own company only) |

Hide or disable buttons in the UI based on these rules, but always handle a 403 from the API.

---

## Auth and Users

### `POST /api/auth/login/`

Authenticate with email and password. **Public**, rate limited.

Request:

```json
{ "email": "user@example.com", "password": "secret" }
```

Response `200`:

```json
{
  "refresh": "<jwt>",
  "access": "<jwt>",
  "user": {
    "id": "uuid", "email": "user@example.com", "full_name": "Ahmed Ali",
    "phone": null, "job_title": null, "user_type": "employee",
    "company_id": "uuid | null", "branch_id": "uuid | null"
  }
}
```

The access token also carries `email`, `company_id` and `branch_id` claims. Wrong credentials or an inactive user return `401`.

### `POST /api/auth/refresh/`

Exchange a refresh token for a new access token. **Public**, rate limited.

Request `{ "refresh": "<jwt>" }` → Response `200` `{ "access": "<jwt>" }`. A deleted or deactivated user gets `401`.

### `GET /api/auth/me/`

Current user profile: `id`, `email`, `full_name`, `phone`, `job_title`, `user_type`, `company_id`, `branch_id`. Any authenticated user.

### `GET /api/auth/context/`

Current user plus names for the header/sidebar. Any authenticated user.

```json
{
  "user": { "...same as /me/..." },
  "company": { "id": "uuid", "name": "Wethaq Co." },
  "branch": { "id": "uuid", "name": "Main Branch" }
}
```

`company` and `branch` are `null` when not assigned.

### User administration — `/api/auth/users/`

**Permission:** system admins (`system_admin` user type or superuser) manage every user. Company admins (`company_admin` user type or CompanyAdmin role) manage users of their own company only; superusers and system admins are invisible to them (404). Everyone else gets 403.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/auth/users/` | List users (inactive users included). |
| POST | `/api/auth/users/` | Create a user. |
| GET | `/api/auth/users/{id}/` | Retrieve a user. |
| PUT / PATCH | `/api/auth/users/{id}/` | Update a user. |
| DELETE | `/api/auth/users/{id}/` | **Deactivate** (sets `is_active=false`, returns `204`). Users are never hard-deleted. |

List query parameters: `search` (email or full name), `user_type` (`system_admin`, `company_admin`, `branch_manager`, `employee`), `company` (UUID), `branch` (UUID), `is_active` (`true`/`false`).

User object:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | uuid | read-only |
| `email` | string | required, unique (case-insensitive) |
| `full_name`, `phone`, `job_title` | string | optional |
| `user_type` | enum | `system_admin`, `company_admin`, `branch_manager`, `employee` |
| `company` | uuid \| null | company admins: always their own company (ignored/forced on create, error if changed) |
| `company_name` | string | read-only |
| `branch` | uuid \| null | must belong to `company` |
| `branch_name` | string | read-only |
| `roles` | string[] | ERP roles. Sending it **replaces** the user's roles; the default role of the `user_type` is always kept. |
| `is_active` | boolean | `PATCH {"is_active": true}` reactivates a user |
| `password` | string | **write-only**. Required on create; on update sets a new password. Checked against Django's password validators and stored hashed. |
| `date_joined`, `last_login` | date-time | read-only |

Create example:

```json
{
  "email": "sara@example.com",
  "full_name": "Sara Hassan",
  "user_type": "employee",
  "branch": "uuid",
  "roles": ["SalesUser", "SalesManager"],
  "password": "a-strong-password"
}
```

Validation errors (`400`): duplicate email; missing password on create; weak password (`{"password": [...]}`); branch outside the company; a company admin assigning `system_admin` (`{"user_type": ...}`) or another company (`{"company": ...}`); deactivating your own account (`{"is_active": ...}`).

---

## Core (Dashboard)

### `GET /api/dashboard/summary/`

Headline numbers for posted documents in the user's company and branch scope. Any company user.

```json
{
  "total_sales": "0.00",
  "total_purchases": "0.00",
  "inventory_items": 0,
  "inventory_quantity": "0.00",
  "customers_receivable": "0.00",
  "suppliers_payable": "0.00",
  "low_stock_products": 0
}
```

`customers_receivable` / `suppliers_payable` are posted invoices minus posted payments (an approximation, not a ledger balance).

---

## Partners

Customers and suppliers. Any company user.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/partners/partners/` | List partners. Query: `partner_type` (`customer`, `supplier`, `both`), `search` (name). |
| POST | `/api/partners/partners/` | Create a partner. |
| GET | `/api/partners/partners/{id}/` | Retrieve. |
| PUT / PATCH | `/api/partners/partners/{id}/` | Update. |
| DELETE | `/api/partners/partners/{id}/` | Soft delete. |
| GET | `/api/partners/partners/customers/` | Partners usable as customers (`customer` or `both`). Use for sales dropdowns. |
| GET | `/api/partners/partners/suppliers/` | Partners usable as suppliers (`supplier` or `both`). Use for purchase dropdowns. |

Partner fields: `name` (required), `partner_type` (default `customer`), `phone`, `mobile`, `email`, `website`, `address`, `city`, `tax_number`, `commercial_record`, `credit_limit`, `initial_balance`, `is_active`, `notes`, `responsible` (user UUID). Read-only: `id`, `company`, `code` (generated: `CUST-`, `SUP-`, `PRT-`), `current_balance`, `created_at`, `updated_at`.

---

## Inventory

### Master data

Any company user. Units are shared across companies; products and warehouses are per company.

| Method | Path | Description |
| --- | --- | --- |
| GET / POST | `/api/inventory/units/` | List (query: `search`) / create units. |
| GET / PUT / PATCH / DELETE | `/api/inventory/units/{id}/` | Unit detail. |
| GET / POST | `/api/inventory/products/` | List (query: `category`, `product_type` = `storable`/`service`/`consumable`, `search`) / create products. |
| GET / PUT / PATCH / DELETE | `/api/inventory/products/{id}/` | Product detail. |
| GET / POST | `/api/inventory/warehouses/` | List (query: `branch`, `warehouse_type` = `main`/`sub`, `search`) / create warehouses. |
| GET / PUT / PATCH / DELETE | `/api/inventory/warehouses/{id}/` | Warehouse detail. |

Key payloads:

- **Unit:** `name` (required), `short_name` (required), `is_active`.
- **Product:** `name` (required), `unit` (required UUID), `category`, `barcode`, `product_type` (default `storable`), `description`, `cost_price`, `sale_price`, `reorder_point`, `income_account`, `expense_account`, `is_active`. Read-only: `id`, `company`, `sku` (generated). `average_cost` is recalculated automatically when inbound stock is posted.
- **Warehouse:** `name` (required), `branch` (required UUID), `warehouse_type` (`main`/`sub`), `keeper` (user UUID), `address`, `is_active`. Read-only: `code`.

### Stock transactions

Manual stock documents (receipts, issues, transfers). Any company user with branch access; posting requires CompanyAdmin or InventoryManager.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/inventory/stock-transactions/` | List. Query: `status` (`draft`, `posted`, `cancelled`), `type` (`IN`, `OUT`, `TRANSFER`). |
| POST | `/api/inventory/stock-transactions/` | Create a draft. |
| GET / PUT / PATCH / DELETE | `/api/inventory/stock-transactions/{id}/` | Detail; update and delete only while draft. |
| POST | `/api/inventory/stock-transactions/{id}/post/` | Post the draft: updates stock balances and weighted average cost (inbound lines with `unit_cost > 0`). Rejects insufficient available quantity. Empty body. Returns the transaction. |
| GET | `/api/inventory/stock-movements/` | List lines. Query: `transaction` (UUID). |
| POST | `/api/inventory/stock-movements/` | Add a line to a draft transaction. |
| GET / PUT / PATCH / DELETE | `/api/inventory/stock-movements/{id}/` | Line detail; only for draft transactions. |

- **Transaction payload:** `transaction_type` (required: `IN`, `OUT`, `TRANSFER`), `source_warehouse` (required), `destination_warehouse` (required for `TRANSFER`, must differ from source; must be empty otherwise), `date`, `reference`, `notes`. Read-only: `id`, `code`, `status`, `posted_by`, `posted_at`, `items` (array of movement lines).
- **Movement payload:** `transaction` (required), `product` (required), `quantity` (required), `unit_cost`, `note`.

### Balances and inventory reports

Any company user; branch users only see their branch's warehouses.

| Method | Path | Query | Response (per row) |
| --- | --- | --- | --- |
| GET | `/api/inventory/stock-balances/` | `product`, `warehouse`, `low_stock` (bool), `search` | `id`, `product`, `warehouse`, `quantity`, `reserved_quantity`, `available_quantity`, `location`, `reorder_point` |
| GET | `/api/inventory/stock-balances/{id}/` | — | one balance |
| GET | `/api/inventory/reports/warehouse-balances/` | `warehouse`, `product`, `low_stock` (bool) | `warehouse_id`, `warehouse_name`, `product_id`, `product_name`, `product_code`, `quantity`, `reorder_point`, `is_low_stock`, `average_cost`, `estimated_value` |
| GET | `/api/inventory/reports/product-movements/` | `product`, `warehouse`, `start_date`, `end_date`, `transaction_type` (`IN`/`OUT`/`TRANSFER`) | `date`, `transaction_id`, `transaction_number`, `reference`, `transaction_type`, `product_id`, `product_name`, `warehouse_id`, `warehouse_name`, `quantity_in`, `quantity_out`, `unit_cost`, `notes` |

---

## Sales

Credit sales invoices. Any company user with branch access can manage drafts; see [roles](#roles-and-permissions) for post/cancel.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/sales/invoices/` | List. Query: `status`, `customer` (UUID), `date_from`, `date_to`. |
| POST | `/api/sales/invoices/` | Create a draft in the user's branch. |
| GET / PUT / PATCH / DELETE | `/api/sales/invoices/{id}/` | Detail; update and delete only while draft. |
| POST | `/api/sales/invoices/{id}/post/` | Post: issues stock for storable products from `warehouse` and creates the journal entry (AR / revenue, COGS / inventory). Empty body. Returns the invoice. **Roles:** CompanyAdmin, SalesManager. |
| POST | `/api/sales/invoices/{id}/cancel/` | Cancel a posted invoice with reversing stock and journal entries. Body: `{"cancellation_reason": "optional text"}`. Returns the invoice. Releases any payment allocations. **Roles:** CompanyAdmin, SalesManager, AccountingManager. |
| GET | `/api/sales/invoice-items/` | List lines. Query: `invoice` (UUID). |
| POST | `/api/sales/invoice-items/` | Add a line to a draft invoice. |
| GET / PUT / PATCH / DELETE | `/api/sales/invoice-items/{id}/` | Line detail; only for draft invoices. |

- **Invoice payload:** `customer` (required), `warehouse` (required before posting when the invoice has stock items), `date`, `notes`.
- **Invoice response adds (read-only):** `id`, `invoice_number`, `company`, `branch`, `status`, `total_amount`, `amount_paid`, `amount_due`, `payment_status` (`unpaid`, `partially_paid`, `paid`), `journal_entry_id`, `posted_by`, `posted_at`, `cancelled_by`, `cancelled_at`, `cancellation_reason`, `items[]`.
- **Item payload:** `invoice` (required), `product` (required), `quantity` (required), `unit_price` (required), `notes`. Read-only: `line_total`.

---

## Purchases

Supplier invoices. Same rules as sales; see [roles](#roles-and-permissions) for post/cancel.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/purchases/invoices/` | List. Query: `status`, `supplier` (UUID), `warehouse` (UUID), `date_from`, `date_to`. |
| POST | `/api/purchases/invoices/` | Create a draft in the user's branch. |
| GET / PUT / PATCH / DELETE | `/api/purchases/invoices/{id}/` | Detail; update and delete only while draft. |
| POST | `/api/purchases/invoices/{id}/post/` | Post: receives stock into `warehouse`, updates weighted average cost, creates the journal entry (inventory / AP). Empty body. **Roles:** CompanyAdmin, PurchaseManager. |
| POST | `/api/purchases/invoices/{id}/cancel/` | Cancel a posted invoice. Body: `{"cancellation_reason": "optional text"}`. Releases any payment allocations. **Roles:** CompanyAdmin, PurchaseManager, AccountingManager. |
| GET | `/api/purchases/invoice-items/` | List lines. Query: `invoice` (UUID). |
| POST | `/api/purchases/invoice-items/` | Add a line to a draft invoice. |
| GET / PUT / PATCH / DELETE | `/api/purchases/invoice-items/{id}/` | Line detail; only for draft invoices. |

- **Invoice payload:** `supplier` (required), `warehouse` (required), `invoice_date`, `vendor_bill_number`, `shipping_cost`, `clearance_cost`, `commission_percentage`, `notes`.
- **Invoice response adds (read-only):** `id`, `invoice_number`, `company`, `branch`, `status`, `total_amount`, `amount_paid`, `amount_due`, `payment_status` (`unpaid`, `partially_paid`, `paid`), `journal_entry_id`, `posted_by`, `posted_at`, `cancelled_by`, `cancelled_at`, `cancellation_reason`, `items[]`.
- **Item payload:** `invoice`, `product`, `quantity`, `unit_price` (all required), `notes`. Read-only: `line_total`.

---

## Accounting

### Account lookup

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/accounting/accounts/` | Active, postable accounts of the company (read-only). Query: `account_type` (`asset`, `liability`, `equity`, `income`, `expense`), `search` (code or name). |
| GET | `/api/accounting/accounts/{id}/` | One account. |

Row: `id`, `code`, `name`, `account_type`, `normal_balance` (`debit`/`credit`), `is_postable`, `is_active`. Any company user.

### Journal entries

`GET /api/accounting/journal-entries/{id}/` — one entry for drill-down from an invoice or payment (`journal_entry_id`). There is no list or create endpoint. Any company user with branch access.

Response: `id`, `entry_number`, `date`, `status`, `reference`, `description`, `journal` `{id, code, name, type}`, `total_debit`, `total_credit`, `items[]` `{id, account_id, account_code, account_name, partner_id, partner_name, debit, credit, description}`.

### Payments

Receipts from customers (`inbound`) and payments to suppliers (`outbound`). Any company user with branch access can manage drafts; the user must have a branch to create one.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/accounting/payments/` | List. Query: `status`, `payment_type` (`inbound`/`outbound`), `payment_method` (`cash`/`bank`), `partner` (UUID). |
| POST | `/api/accounting/payments/` | Create a draft. |
| GET / PUT / PATCH / DELETE | `/api/accounting/payments/{id}/` | Detail; update and delete only while draft. |
| POST | `/api/accounting/payments/{id}/post/` | Post: inbound debits cash/bank and credits AR; outbound debits AP and credits cash/bank. Outbound payments are rejected if the cash/bank balance is insufficient. Empty body. **Roles:** CompanyAdmin, Accountant, AccountingManager. |
| POST | `/api/accounting/payments/{id}/cancel/` | Cancel a posted payment with a reversing entry. Body: `{"cancellation_reason": "optional text"}`. Releases its allocations. **Roles:** CompanyAdmin, AccountingManager. |
| POST | `/api/accounting/payments/{id}/allocate/` | Allocate to an invoice — see below. |

- **Payment payload:** `partner` (required), `payment_type` (required), `payment_method` (required), `account` (required: the cash or bank account UUID from the account lookup), `amount`, `date`, `reference`, `notes`.
- **Response adds (read-only):** `id`, `voucher_number`, `company`, `branch`, `status`, `allocated_amount`, `unallocated_amount`, `journal_entry_id`, `posted_by`, `posted_at`, `cancelled_by`, `cancelled_at`, `cancellation_reason`, `created_at`, `updated_at`.

### Payment allocation — `POST /api/accounting/payments/{id}/allocate/`

Settle a specific invoice (fully or partially) with a posted payment. Can be called several times to split one payment across invoices.

**Roles:** CompanyAdmin, Accountant, AccountingManager. Branch-scoped users can only allocate payments and invoices of their branch.

Request:

```json
{
  "invoice_id": "uuid",
  "invoice_type": "sales",
  "amount": "500.00"
}
```

`invoice_type` is `sales` or `purchase`.

Response `201`:

```json
{
  "id": "uuid",
  "payment": "uuid",
  "invoice_type": "sales",
  "invoice_id": "uuid",
  "invoice_number": "INV-0001",
  "amount": "500.00",
  "invoice_amount_paid": "500.00",
  "invoice_amount_due": "750.00",
  "invoice_payment_status": "partially_paid",
  "payment_unallocated_amount": "0.00",
  "created_at": "2026-10-04T12:00:00Z"
}
```

Rules (violations return `400`):

- Payment and invoice are both `posted`, in the same company, for the same partner.
- Inbound payments only allocate to sales invoices; outbound payments only to purchase invoices.
- `amount` > 0 with at most 2 decimal places, and not more than the payment's `unallocated_amount` or the invoice's `amount_due`.

Cancelling the payment or the invoice releases its allocations and reduces the invoice's `amount_paid`. After allocating, refresh the payment and invoice to show the new `unallocated_amount`, `amount_paid`, `amount_due` and `payment_status`.

### Financial reports

All reports are `GET`, read posted journal items only, and are limited to the user's branch unless the user has company-wide access (a branch-scoped user without a branch gets 403).

**Roles:** CompanyAdmin, Accountant, AccountingManager, Auditor.

Common query parameters: `start_date`, `end_date` (both optional, `YYYY-MM-DD`; `start_date` must not be after `end_date`).

Section object used below:

```json
{
  "account_type": "asset",
  "label": "Assets",
  "accounts": [
    { "account_id": "uuid", "code": "1001", "name": "Cash", "balance": "1500.00" }
  ],
  "total": "1500.00"
}
```

Balances are signed by the account's normal side (positive = normal balance).

#### `GET /api/accounting/reports/trial-balance/`

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-12-31",
  "sections": [
    {
      "account_type": "asset", "label": "Assets",
      "accounts": [
        {
          "account_id": "uuid", "code": "1001", "name": "Cash", "normal_balance": "debit",
          "total_debit": "2000.00", "total_credit": "500.00",
          "debit_balance": "1500.00", "credit_balance": "0.00", "balance": "1500.00"
        }
      ],
      "total_debit": "2000.00", "total_credit": "500.00",
      "debit_balance": "1500.00", "credit_balance": "0.00"
    }
  ],
  "totals": {
    "total_debit": "...", "total_credit": "...",
    "debit_balance": "...", "credit_balance": "...",
    "is_balanced": true
  }
}
```

#### `GET /api/accounting/reports/income-statement/`

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-12-31",
  "income":   { "...section...": "" },
  "expenses": { "...section...": "" },
  "net_profit": "1200.00"
}
```

`net_profit` is negative for a loss.

#### `GET /api/accounting/reports/balance-sheet/`

Balances as of `end_date`.

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-12-31",
  "assets":      { "...section...": "" },
  "liabilities": { "...section...": "" },
  "equity": {
    "...section...": "",
    "retained_earnings": "300.00",
    "net_profit": "1200.00"
  },
  "total_liabilities_and_equity": "...",
  "is_balanced": true
}
```

`retained_earnings` is profit before `start_date`; `net_profit` is profit inside the range. Both are included in `equity.total`, so `assets.total == total_liabilities_and_equity`.

#### `GET /api/accounting/reports/general-ledger/`

Extra query parameters: `account` (UUID), `partner` (UUID).

Response: array of `{date, journal_entry_id, entry_number, reference, account_code, account_name, partner, debit, credit, running_balance}`.

---

## AI Assistant

Document Q&A over uploaded PDF/DOCX files. Any company user; documents are company-scoped. Processing needs the AI packages; `ask` also needs a local Ollama server.

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/ai-assistant/documents/` | List documents. |
| POST | `/api/ai-assistant/documents/` | Upload (`multipart/form-data`: `file` = PDF or DOCX, max 20 MB by default; `notes` optional). Returns status `uploaded`. |
| GET | `/api/ai-assistant/documents/{id}/` | Retrieve. |
| DELETE | `/api/ai-assistant/documents/{id}/` | Delete document, chunks and index. |
| POST | `/api/ai-assistant/documents/{id}/process/` | Extract text, chunk, embed and index. Returns the document (`status`: `processing` → `ready` / `failed`). |
| GET | `/api/ai-assistant/documents/{id}/chunks/` | Extracted chunks `{id, chunk_index, text, page_number, char_start, char_end}`. |
| POST | `/api/ai-assistant/documents/{id}/search/` | Semantic search. Body `{"query": "...", "top_k": 5}` → `[{score, chunk}]`. |
| POST | `/api/ai-assistant/documents/{id}/keyword-search/` | Keyword search. Body `{"query": "...", "top_k": 5}` → `[{chunk_id, chunk_index, page_number, text, score, method}]`. |
| POST | `/api/ai-assistant/documents/{id}/ask/` | Question answering. Body `{"question": "...", "top_k": 5}` → `{answer, citations: [{chunk_id, chunk_index, page_number, text, score}]}`. |

Document fields: `id`, `company`, `uploaded_by`, `file` (URL), `original_filename`, `file_type`, `file_size`, `status` (`uploaded`, `processing`, `ready`, `failed`), `notes`, `chunks_count`, `created_at`, `updated_at`.

---

## System endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/health/` | public | `{"status": "ok"}` — load balancer health check. |
| GET | `/` | public | HTML landing page (not JSON); links to `/admin/`. |
| GET | `/api/schema/` | public in DEBUG, staff-only in production | OpenAPI 3 schema (YAML; `?format=json` for JSON). |
| GET | `/api/docs/` | same | Swagger UI. |
| GET | `/api/redoc/` | same | ReDoc. |

In production the docs can be removed entirely with `API_DOCS_ENABLED=False`.
