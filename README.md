# ERP System

Django + React ERP MVP for multi-company operations. The backend is the source
of business truth and exposes REST APIs; the frontend is a Vite/React
operational UI for the current MVP workflows.

## Current MVP Scope

Implemented backend domains:

- Multi-company and branch-aware users, partners, products, warehouses, and
  documents.
- Inventory workflow with stock transactions, stock movements, stock balances,
  stock posting, insufficient-stock checks, transfers, and weighted average cost
  updates on inbound stock.
- Sales invoice workflow with draft invoices, invoice items, posting, stock
  reduction for stock products, accounting journal creation, and cancellation
  via reversing stock/journal entries.
- Purchase invoice workflow with draft invoices, invoice items, posting,
  inventory increase, weighted average cost updates, and accounting journal
  creation, and cancellation via reversing stock/journal entries.
- Payment workflow with draft inbound/outbound payments, cash/bank selection,
  posting, journal creation, and cancellation via reversing journal entries.
- Accounting workflow with chart of accounts, journals, journal entries,
  journal items, journal entry detail API, posted-entry immutability, and
  payment/invoice posting entries.
- Dashboard API with posted sales, posted purchases, inventory quantity,
  receivable/payable summary, and low-stock count.
- AI Assistant module for document upload, processing, retrieval comparison, and
  question answering.

Implemented frontend areas:

- Authenticated layout with sidebar, navbar, footer, and protected routes.
- Auto logout after 30 minutes of inactivity.
- Dashboard summary.
- Partners, products, warehouses, stock transactions, stock balances, stock
  movements.
- Purchase invoices: list, create draft, details, add items, post.
- Sales invoices: list, create draft, details, add items, post.
- Payments: list, create draft inbound/outbound payment, select cash/bank
  account, post.
- Journal entry drill-down from posted invoices and payments.
- AI Assistant page.

## Accounting Behavior

Sales invoice posting:

- Reduces stock for non-service products through an `OUT` stock transaction.
- Creates a posted sales journal entry.
- Debits Accounts Receivable (`1003`) for the customer.
- Credits Sales Revenue (`4001`).
- Debits Cost of Goods Sold (`5001`) for stock products using product average
  cost.
- Credits Inventory (`1004`) for the same cost amount.
- Service products do not create stock movements or COGS/inventory lines.

Purchase invoice posting:

- Increases inventory through an `IN` stock transaction.
- Updates weighted average cost from incoming quantities and unit prices.
- Creates a posted purchase journal entry.
- Debits Inventory (`1004`).
- Credits Accounts Payable (`2001`) for the supplier.

Payment posting:

- Supports inbound customer receipts and outbound supplier payments.
- Uses cash or bank journals/accounts based on selected payment method/account.
- Inbound payment debits the selected cash/bank asset account and credits
  Accounts Receivable (`1003`) for the partner.
- Outbound payment debits Accounts Payable (`2001`) for the partner and credits
  the selected cash/bank asset account.
- Payments settle AR/AP at partner-account balance level only. They are not yet
  allocated to specific invoices.

Reversal behavior:

- Posted sales invoices can be cancelled through the backend/API/admin; this
  marks the invoice cancelled, creates a reversing journal entry, and restores
  stock for stock products through an inbound reversal transaction.
- Posted purchase invoices can be cancelled through the backend/API/admin; this
  marks the invoice cancelled, creates a reversing journal entry, and removes
  stock through an outbound reversal transaction.
- Posted payments can be cancelled through the backend/API/admin; this marks the
  payment cancelled and creates a reversing journal entry.
- Frontend operational pages show cancelled status and journal drill-down links,
  but do not yet expose cancel buttons.

## Important MVP Limitations

- Sales invoices are credit-only in the MVP. There is no cash sale mode at
  invoice creation.
- Frontend cancel actions are not exposed yet; cancellation is available through
  backend API/admin for sales invoices, purchase invoices, and payments.
- Journal entry drill-down is detail-only. There is no full journal browser UI.
- Payment allocation to specific invoices is missing.
- Permissions are mostly authenticated-user/company scoped, not full role-based
  permissions.
- Branch scoping is incomplete in some list/report surfaces.
- Inventory valuation is weighted-average only and lacks period close, landed
  cost allocation, valuation layers, and audit reports.
- Financial and inventory reports are missing beyond the dashboard summary.

## Release Validation

Current same-day submission validation:

- Backend: `python manage.py check` passed with no issues.
- Backend: `python manage.py test` passed, 120 tests run, 2 skipped.
- Frontend: `npm.cmd run build` passed.

## Tech Stack

- Backend: Django, Django REST Framework, PostgreSQL, SimpleJWT,
  drf-spectacular.
- Frontend: React, TypeScript, Vite, React Router, Axios, Zustand.
- AI Assistant: PDF/DOCX ingestion, FAISS/sentence-transformers/LangChain/Ollama
  stack.

## Run Backend

```powershell
cd backend
pip install -r requirements.txt
python manage.py check
python manage.py runserver 9000
```

API documentation:

- `GET /api/schema/`
- `GET /api/docs/`
- `GET /api/redoc/`

## Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Documentation

- Master project context: `ERP_SYSTEM_CONTEXT.md`
- Backend API roadmap: `backend/API_ROADMAP.md`
- Frontend documentation: `frontend/README.md`
- AI Assistant module details: `backend/apps/ai_assistant/README.md`
