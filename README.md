# TRUST ERP

Commercial ERP for multi-company, multi-branch operations. The Django backend is the source of business truth and exposes a JWT-protected REST API. The React frontend is the operational UI for the workflows that are wired today.

The UI brand in the sidebar is **TRUST ERP**. Navigation labels are Arabic. Most operational pages are English, with some Arabic titles (general ledger, users placeholder).

## Project Overview

The system covers company and branch setup, partners, inventory, sales invoices, purchase invoices, cash and bank payments, double-entry accounting, a dashboard, and a document question-answering assistant.

Documents move through `draft` → `posted` → `cancelled`. Posting sales, purchases, stock transactions, and payments creates inventory effects and balanced journal entries. Cancelling a posted sales invoice, purchase invoice, or payment creates a reversing journal entry and, for stock products, a reversing stock transaction.

Company data is scoped to the authenticated user's company. Branch users are further scoped to their branch. Company-wide roles can see all branches of that company.

Master data such as companies, branches, users, chart of accounts, journals, units, and categories is maintained in the Django admin (Unfold). The React app operates the day-to-day documents and reports listed below.

## Tech Stack

### Backend

Pinned in `backend/requirements.txt`:

| Area | Packages |
| --- | --- |
| Framework | Django 6.0.2, Django REST Framework 3.16.1 |
| Database | PostgreSQL via `psycopg2-binary` 2.9.11 |
| Auth | `djangorestframework-simplejwt` 5.5.1, PyJWT 2.11.0 |
| API schema | `drf-spectacular` 0.27.2 (OpenAPI, Swagger, ReDoc) |
| Admin | `django-unfold` 0.79.0 |
| HTTP / deploy | `django-cors-headers` 4.9.0, WhiteNoise 6.11.0, Gunicorn 23.0.0 |
| Other | Pillow, `python-dotenv` |
| AI documents | `pypdf`, `python-docx`, `sentence-transformers`, `faiss-cpu`, LangChain, `langchain-community`, `langchain-ollama`, `ollama` |

Django 6.0 requires Python 3.12 or newer.

List and report filters are implemented with serializers and queryset parameters.

### Frontend

From `frontend/package.json`:

| Area | Packages |
| --- | --- |
| UI | React 19, React DOM 19 |
| Build | Vite 8, TypeScript 6, `@vitejs/plugin-react` |
| Routing | React Router 7 |
| Data / state | Axios, Zustand (persisted auth store) |
| Feedback | `react-hot-toast` |
| Lint | ESLint 9, `typescript-eslint`, React Hooks and React Refresh plugins |

There is no CSS framework and no component library. Layout and pages use inline styles plus `src/index.css` and `src/styles/theme.ts`.

### Runtime services

- PostgreSQL database.
- For the AI assistant only: a local [Ollama](https://ollama.com/) server with the `llama3` model. Uploading and processing documents uses local embeddings and FAISS and does not call Ollama. Asking a question does.

## Project Structure

```text
erp_system/
├── README.md
├── ERP_SYSTEM_CONTEXT.md
├── BACKEND_ANALYSIS.md
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   └── apps/
│       ├── core/            # company, branch, sequences, audit, fiscal year, settings, dashboard
│       ├── users/           # custom user, JWT auth, roles, permissions
│       ├── partners/        # customers and suppliers
│       ├── inventory/       # products, warehouses, stock documents, balances, reports
│       ├── sales/           # sales invoices and posting/cancellation service
│       ├── purchases/       # purchase invoices and posting/cancellation service
│       ├── accounting/      # chart, journals, entries, payments, financial reports
│       └── ai_assistant/    # PDF/DOCX upload, embeddings, FAISS, Q&A
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── app/             # layout, protected routes, Zustand auth store
        ├── components/      # navbar, sidebar, footer, shared MVP UI, Guard
        ├── features/        # one folder per operational screen and its API client
        ├── hooks/           # inactivity auto-logout
        ├── lib/api/         # Axios client, endpoints, login, errors
        ├── pages/           # login, users placeholder
        └── styles/
```

Frontend feature folders: `dashboard`, `partners`, `products`, `warehouses`, `stock-transactions`, `stock-balances`, `stock-movements`, `inventory` (reports), `sales-invoices`, `purchase-invoices`, `payments`, `accounting`, `ai-assistant`, `auth`.

## Implemented Modules & Features

### Backend apps

| App | API prefix | What it does |
| --- | --- | --- |
| `core` | `/api/dashboard/summary/` | Company-scoped dashboard totals. Admin for companies, branches, fiscal years, sequences, attachments, audit log, system settings. |
| `users` | `/api/auth/` | Email login, refresh, current user, company/branch context, user administration. Role groups and action permissions. |
| `partners` | `/api/partners/` | Partner CRUD, plus customer and supplier list actions. |
| `inventory` | `/api/inventory/` | Units, products, warehouses, stock transactions, movements, balances, two reports. |
| `sales` | `/api/sales/` | Sales invoices and line items, post, cancel. |
| `purchases` | `/api/purchases/` | Purchase invoices and line items, post, cancel. |
| `accounting` | `/api/accounting/` | Account lookup, journal-entry detail, payments, general ledger, trial balance, income statement, balance sheet. |
| `ai_assistant` | `/api/ai-assistant/` | Document upload, process, search, and question answering. |

Root routes outside `/api/`:

- `GET /` — branded "Wethaq ERP" HTML landing page with a link to the admin panel
- `GET /health/` — `{"status": "ok"}`
- `/admin/` — Unfold admin
- `GET /api/schema/`, `/api/docs/`, `/api/redoc/` — OpenAPI, Swagger, ReDoc (public with `DEBUG=True`, staff-only otherwise; `API_DOCS_ENABLED=False` removes them)

Default API permission is authenticated. Login and token refresh are public. In `DEBUG`, the schema views are also public.

### Auth and authorization

- Custom user model: email is the username. Fields include full name, phone, job title, `user_type` (`system_admin`, `company_admin`, `branch_manager`, `employee`), company, and branch.
- `POST /api/auth/login/` returns SimpleJWT access and refresh tokens. Access lifetime is 60 minutes. Refresh lifetime is 7 days.
- `POST /api/auth/refresh/`, `GET /api/auth/me/`, `GET /api/auth/context/`.
- `/api/auth/users/` — user administration (list, retrieve, create, update, partial update; `DELETE` sets `is_active=false` and never hard-deletes; `PATCH {"is_active": true}` reactivates). Only system admins (superuser or `user_type=system_admin`) and company admins (`user_type=company_admin` or the CompanyAdmin group) have access. Company admins only see and manage users of their own company, never superusers or system admins, cannot assign `system_admin`, and cannot move users to another company. Passwords are write-only, required on create, checked against Django's password validators, and hashed. `roles` replaces the user's ERP role groups; the user type's default role (CompanyAdmin or BranchManager) is always added. Admins cannot deactivate themselves.
- `python manage.py setup_roles` creates Django groups: CompanyAdmin, BranchManager, SalesUser, SalesManager, PurchaseUser, PurchaseManager, InventoryUser, InventoryManager, Accountant, AccountingManager, Auditor, AIUser, AIAdmin.
- Company-wide access: superuser, `system_admin`, `company_admin`, CompanyAdmin, AccountingManager, Auditor.
- Action permissions gate posting and cancelling sales invoices, purchase invoices, payments, and stock transactions, and viewing accounting reports.
- There is no user-management REST API. Users are created in the admin.

### Partners

`Partner` types: customer, supplier, or both. Codes are generated (`CUST-`, `SUP-`, `PRT-`). The API is a full viewset, plus `GET /api/partners/partners/customers/` and `GET /api/partners/partners/suppliers/`.

The React partners page lists partners and shows counts. It does not create or edit them.

### Inventory

Master data API (full CRUD): units, products, warehouses.

Product types: `storable`, `service`, `consumable`. SKU is generated (`PROD-`) when blank. Products store cost, weighted average cost, sale price, reorder point, and optional income and expense accounts. Posting services use the standard chart codes below; they do not read those product account fields.

Warehouses belong to a branch and are `main` or `sub`. Codes use the `WH-` prefix.

Stock documents:

- Types: `IN`, `OUT`, `TRANSFER`.
- Status: `draft`, `posted`, `cancelled`.
- `POST /api/inventory/stock-transactions/{id}/post/` posts a draft, updates `StockBalance`, rejects insufficient available quantity, and updates weighted average cost on inbound quantity when unit cost is greater than zero.
- Transfers require a different destination warehouse.
- Service products cannot be stock movement lines.
- Stock balances are list/retrieve only. They are updated by the stock service, not by direct client writes.

Reports:

- `GET /api/inventory/reports/product-movements/` — posted movements, filterable by product, warehouse, date range, and transaction type. Branch users see their branch.
- `GET /api/inventory/reports/warehouse-balances/` — current balances, filterable by warehouse, product, and low stock.

React pages for products, warehouses, stock transactions, stock balances, and stock movements are searchable/filterable lists. Creating and posting stock documents is done through the API or admin. Product movement history and warehouse balances are filterable report pages.

### Sales invoices

- Draft invoice, line items (quantity, unit price, computed line total), post, cancel.
- Invoice numbers: `SINV-` per branch.
- Posting a draft with a positive total creates an `OUT` stock transaction for non-service lines, using product average cost, then a posted sales journal.
- A warehouse is required only when the invoice contains stock lines.
- Service lines do not move stock and do not create COGS.
- Cancellation of a posted invoice restores stock with an inbound reversal and posts a reversing journal entry.
- Sales invoices are credit sales. There is no cash-sale mode.

Journal on post (standard chart codes):

- Debit Accounts Receivable `1003` (customer partner on the line).
- Credit Sales Revenue `4001`.
- Debit Cost of Goods Sold `5001` and credit Inventory `1004` when stock COGS is greater than zero.

The React flow is list, create draft, open details, add lines while draft, post, and cancel/reverse a posted invoice, with a link to the journal entry.

### Purchase invoices

- Draft invoice, line items, post, cancel.
- Invoice numbers: `PINV-` per branch.
- Header fields include supplier bill number, shipping cost, clearance cost, and a supplier commission percentage.
- Posting creates an `IN` stock transaction. Shipping and clearance are added to the invoice total and allocated into unit cost. Weighted average cost is updated from those allocated costs.
- `commission_percentage` is stored and exposed by the serializer. It is not added to `total_amount` and is not posted to the ledger.
- Cancellation of a posted invoice issues an outbound stock reversal and a reversing journal entry.

Journal on post:

- Debit Inventory `1004` for the invoice total.
- Credit Accounts Payable `2001` for the supplier.

The React flow matches sales: list, create, details, add lines, post, cancel/reverse, journal drill-down.

### Payments

- Types: `inbound` (customer receipt) and `outbound` (supplier payment).
- Methods: `cash` or `bank`.
- The selected account must be an active, postable asset account.
- Voucher numbers are generated per branch.
- Posting writes a journal in the cash journal (`CSH`) or bank journal (`BNK`) and uses the selected cash/bank account.
- Inbound: debit cash/bank, credit Accounts Receivable `1003` for the partner.
- Outbound: debit Accounts Payable `2001` for the partner, credit cash/bank. Outbound posting is rejected when the cash/bank account balance is lower than the amount.
- Cancellation posts a reversing journal entry. It does not move stock.
- Payments settle partner AR/AP at account level. They can also be allocated to specific invoices with `POST /api/accounting/payments/{id}/allocate/` (`invoice_id`, `invoice_type` = `sales` or `purchase`, `amount`). Rules: payment and invoice both posted, same company and partner, inbound payments only to sales invoices and outbound only to purchase invoices, and the amount cannot exceed the payment's unallocated balance or the invoice's outstanding balance. Requires CompanyAdmin, Accountant, or AccountingManager; branch-scoped users can only allocate to invoices of their branch.
- Allocation writes no journal entry (the AR/AP posting already happened); it only tracks settlement. Invoices expose `amount_paid`, `amount_due`, and `payment_status` (`unpaid`, `partially_paid`, `paid`); their `status` stays `posted`. Payments expose `allocated_amount` and `unallocated_amount`.
- Cancelling a payment or an invoice releases its allocations and reduces the invoices' `amount_paid` accordingly.

The React payments page lists payments, creates a draft, posts it, cancels/reverses a posted payment, and links to the journal entry. Summary cards count received, paid, and draft payments.

### Accounting

Models: chart of accounts (tree), journals (`sale`, `purchase`, `cash`, `bank`, `general`), journal entries, journal lines, payments, payment allocations.

Posted and cancelled journal entries are immutable. Corrections are reversing entries. A posted entry must be balanced and non-zero.

Migration `accounting.0005` seeds this chart per company:

| Code | Name | Type | Postable |
| --- | --- | --- | --- |
| 1000 | Assets | asset | no |
| 1001 | Bank | asset | yes |
| 1002 | Cash | asset | yes |
| 1003 | Accounts Receivable | asset | yes |
| 1004 | Inventory | asset | yes |
| 2000 | Liabilities | liability | no |
| 2001 | Accounts Payable | liability | yes |
| 3000 | Equity | equity | no |
| 3001 | Owner Capital | equity | yes |
| 4000 | Income | income | no |
| 4001 | Sales Revenue | income | yes |
| 5000 | Expenses | expense | no |
| 5001 | Cost of Goods Sold | expense | yes |
| 5002 | Operating Expenses | expense | yes |
| 5003 | Purchase Expenses | expense | yes |

API:

- `GET /api/accounting/accounts/` — lookup of active postable accounts (read-only).
- `GET /api/accounting/journal-entries/{id}/` — one entry with its lines. There is no journal-entry list or create API.
- `GET /api/accounting/reports/general-ledger/` — posted journal lines, filterable by start date, end date, account, and partner.
- `GET /api/accounting/reports/trial-balance/` — debit and credit totals, net debit/credit balance, and normal-side balance per account for the date range, in sections by account type, with grand totals and an `is_balanced` flag.
- `GET /api/accounting/reports/income-statement/` — income and expense accounts for the date range, section totals, and `net_profit` (negative for a loss).
- `GET /api/accounting/reports/balance-sheet/` — asset, liability, and equity balances as of `end_date`. Equity also carries `retained_earnings` (profit before `start_date`) and `net_profit` (profit inside the range), so assets equal liabilities plus equity.

All four reports accept `start_date` and `end_date`, use posted, non-deleted entries of the user's company only, and require an accounting-report role (CompanyAdmin, Accountant, AccountingManager, Auditor, or a company-wide user type / superuser). Branch-scoped users (Accountant) only see entries linked to their branch through a payment, invoice, or stock transaction; manual journal entries are company-wide only. A branch-scoped user with no branch gets 403.

The React general ledger page calls that report and filters by date, account, and partner. The journal entry page is a detail view opened from invoices and payments.

The sidebar still shows Trial Balance, Balance Sheet, and Income Statement as disabled “coming soon” items; the APIs exist but there are no React pages for them yet.

### Dashboard

`GET /api/dashboard/summary/` returns, for posted documents in the user's company and branch scope:

- total sales
- total purchases
- distinct inventory products
- inventory quantity
- customers receivable (`posted sales − posted inbound payments`)
- suppliers payable (`posted purchases − posted outbound payments`)
- low-stock balance count (`quantity <= reorder_point`)

The React dashboard shows those metrics and also loads invoice, payment, and stock-balance lists for status counts and comparisons. Receivable and payable figures are operational summaries, not a full subledger.

### AI assistant

Isolated from ERP posting. It does not write accounting, inventory, sales, or purchase records.

- Upload PDF or DOCX.
- Process: extract text, chunk, embed with `sentence-transformers`, build a local FAISS index.
- List chunks, semantic search, keyword search, delete (file, chunks, and FAISS index).
- Ask a question: retrieve chunks and answer with Ollama `llama3`, returning citations.

Endpoints under `/api/ai-assistant/documents/`: list/create, `DELETE {id}/`, `POST {id}/process/`, `GET {id}/chunks/`, `POST {id}/search/`, `POST {id}/keyword-search/`, `POST {id}/ask/`.

The React page uploads, processes, deletes, asks questions, and compares keyword vs semantic retrieval.

### Frontend routes

Public: `/login`.

Protected (JWT in the Zustand store; Axios sends `Authorization: Bearer`):

| Path | Page |
| --- | --- |
| `/` | Redirects to `/dashboard` |
| `/dashboard` | Dashboard |
| `/partners` | Partner list |
| `/products` | Product list with search and type filter |
| `/warehouses` | Warehouse list |
| `/stock-transactions` | Stock document list |
| `/stock-balances` | Balance list |
| `/stock-movements` | Movement lines |
| `/product-movements` | Product movement history report |
| `/warehouse-balances` | Warehouse balance report |
| `/purchase-invoices` | Purchase invoice list |
| `/purchase-invoices/new` | Create draft |
| `/purchase-invoices/:id` | Details, add lines, post, cancel |
| `/sales-invoices` | Sales invoice list |
| `/sales-invoices/new` | Create draft |
| `/sales-invoices/:id` | Details, add lines, post, cancel |
| `/payments` | Payments |
| `/general-ledger` | General ledger |
| `/accounting/journal-entries/:id` | Journal entry detail |
| `/ai-assistant` | AI assistant |

`AppLayout` logs the user out after 30 minutes without mouse, keyboard, click, scroll, or touch activity. That timer is independent of the API access-token lifetime (60 minutes) and of `SystemSetting.session_timeout_minutes` (default 60, stored for admin settings, not read by the React timer).

`UsersPage` (`/src/pages/UsersPage.tsx`) is a static Arabic placeholder routed at `/users` for `system_admin` and `company_admin` user types. It does not call `/api/auth/users/` yet. `Guard` and `ProtectedRoute` check `user.user_type` from the auth store.

### Not implemented

- React pages for the trial balance, balance sheet, and income statement (the APIs exist).
- A React screen for payment allocation (the API exists).
- Cash sales at invoice time.
- Frontend create/edit screens for partners, products, warehouses, and stock documents.
- A working users page (the user administration API exists).
- Using product income/expense accounts, or purchase commission, in automatic journals.
- Fiscal-year close. `FiscalYear` exists in the admin and is not enforced by posting services.
- VAT calculation. `SystemSetting.default_vat_percentage` is stored and not applied to invoices.

## Database Schema Summary

Most business models use a UUID primary key through `BaseModel` (`created_at`, `updated_at`, `created_by`, `updated_by`) and write an `AuditLog` row on create and update. `SoftDeleteModel` adds `is_deleted`, `deleted_at`, and `deleted_by`. Uniqueness constraints on codes usually ignore soft-deleted rows.

`User` and `Sequence` do not use that base. Users are deactivated with `is_active` instead of soft delete. `AuditLog`, `DocumentChunk`, and `Attachment` are separate tables.

| Model | App | Role |
| --- | --- | --- |
| `Company` | core | Legal entity: name, logo, tax number, commercial record, contact, address. |
| `Branch` | core | Belongs to a company. Auto code `BR-`. Address, phone, active flag. |
| `FiscalYear` | core | Named period per company. One active year per company. `is_closed` is stored. |
| `Sequence` | core | Locked counter used for document numbers. |
| `SystemSetting` | core | Singleton: system name, maintenance flag, currency (default EGP), VAT percent, decimals, session timeout. |
| `AuditLog` | core | Generic create/update/delete/restore log with JSON changes. |
| `Attachment` | core | Generic file attached to any model. |
| `User` | users | Email login, company, branch, user type. |
| `Partner` | partners | Customer, supplier, or both. Credit limit, opening balance, tax data. `current_balance` is computed from posted journal lines. |
| `Unit` | inventory | Global unit name and short name. |
| `Category` | inventory | Company product category tree. |
| `Product` | inventory | Company product card: type, SKU, barcode, prices, average cost, reorder point, optional GL accounts. |
| `Warehouse` | inventory | Company warehouse on a branch, with an optional keeper. |
| `StockTransaction` | inventory | IN / OUT / TRANSFER document. Optional link to one journal entry. |
| `StockMovement` | inventory | Line: product, quantity, unit cost. |
| `StockBalance` | inventory | Quantity, reserved quantity, location, reorder point per company, product, and warehouse. |
| `SalesInvoice` | sales | Branch, customer, optional warehouse, status, total, amount paid, journal entry, post/cancel audit fields. |
| `SalesInvoiceItem` | sales | Product, quantity, unit price, line total. |
| `PurchaseInvoice` | purchases | Branch, supplier, warehouse, vendor bill number, shipping, clearance, commission percent, status, total, amount paid, journal entry. |
| `PurchaseInvoiceItem` | purchases | Product, quantity, unit price, line total. |
| `Account` | accounting | Company chart node: code, type, normal balance, parent, postable, reconciliation flag. |
| `Journal` | accounting | Named book with a type and optional default account. |
| `JournalEntry` | accounting | Draft, posted, or cancelled entry in a journal. |
| `JournalItem` | accounting | Account, optional partner, description, debit, credit. |
| `Payment` | accounting | Inbound/outbound voucher, cash or bank account, amount, journal entry, post/cancel audit fields. |
| `PaymentAllocation` | accounting | Soft-deletable link from a payment to a sales or purchase invoice (generic foreign key) with the allocated amount. |
| `Document` | ai_assistant | Uploaded PDF/DOCX and processing status. |
| `DocumentChunk` | ai_assistant | Chunk text, page span, JSON embedding, embedding model name. |

## Setup & Installation

### Backend

1. Install Python 3.12+ and PostgreSQL. Create a database (the sample name is `erp_db`).
2. From `backend/`, create a virtual environment and install dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Copy `backend/.env.example` to `backend/.env`. Local values:

```text
DEBUG=True
SECRET_KEY=change-me-to-a-long-random-secret
DB_NAME=erp_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_ALL_ORIGINS=False
```

`settings.py` builds the database connection from the `DB_*` variables. With `DEBUG=False` the app refuses to start unless `SECRET_KEY` (at least 50 random characters), `ALLOWED_HOSTS` (no `*`), `DB_NAME`, `DB_USER`, `DB_PASSWORD` and `DB_HOST` are set; `CORS_ALLOW_ALL_ORIGINS` cannot be true, and `DEBUG=True` is rejected when `APP_ENV=Production`. Session and CSRF cookies are always Secure, and the browsable API is disabled. See `backend/.env.example` for every variable.

4. Migrate and create an admin user. Role groups and their permissions are synced automatically after every `migrate`; `python manage.py setup_roles` re-runs the sync manually.

```powershell
python manage.py migrate
python manage.py createsuperuser
```

5. Run the API on port **9000**. The frontend client is hardcoded to `http://127.0.0.1:9000/api`.

```powershell
python manage.py runserver 9000
```

6. In `/admin/`, create a company, branch, and a non-superuser linked to that company (and branch, unless the user is a company-wide admin). Assign the role groups that match the work they should post or cancel. The standard chart of accounts is created automatically when a company is created (migration `0005` seeded companies that already existed); posting looks up codes `1001`–`1004`, `2001`, `4001`, and `5001`.

API docs (when `DEBUG=True`): [http://127.0.0.1:9000/api/docs/](http://127.0.0.1:9000/api/docs/).

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Vite’s default dev server is [http://localhost:5173](http://localhost:5173). `npm run build` runs `tsc -b` and then the production build. `npm run lint` runs ESLint.

Sign in with the email and password of a user that has a company. The access token is stored by Zustand and sent on later API calls.

### AI assistant

Processing and search need the Python AI packages from `requirements.txt` (sentence-transformers and FAISS download or load a local embedding model on first use). Question answering also needs Ollama running locally with `llama3` pulled. Uploaded files are stored under the Django media directory.

### Other docs in the repo

- `ERP_SYSTEM_CONTEXT.md` — longer project context. Treat this README as the description of the code that is present now.
- `frontend/README.md` — frontend route and UI notes.
- `frontend/API_REFERENCE.md` — endpoint, payload and permission reference for the frontend.
- `backend/apps/ai_assistant/README.md` — AI pipeline and request examples.
