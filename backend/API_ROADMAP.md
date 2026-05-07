# API Roadmap - ERP V1

## Overview
This document lists the available backend API endpoints for ERP V1.

### Current Scope
- Auth
- Partners
- Inventory
- Sales
- Purchases
- API documentation via Swagger / ReDoc

### Notes
- The system is multi-company / multi-branch.
- Business logic is handled in services.
- Any document after posting is not editable.
- Posting endpoints execute the actual business flow.

---

## Auth
- POST `/api/auth/login/`
- POST `/api/auth/refresh/`
- GET `/api/auth/me/`
- GET `/api/auth/context/`

---

## Partners

### Partners
- GET `/api/partners/partners/`
- POST `/api/partners/partners/`
- GET `/api/partners/partners/{id}/`
- PATCH `/api/partners/partners/{id}/`

### Partner Lookups
- GET `/api/partners/partners/customers/`
- GET `/api/partners/partners/suppliers/`

---

## Inventory

### Units
- GET `/api/inventory/units/`
- POST `/api/inventory/units/`
- GET `/api/inventory/units/{id}/`
- PATCH `/api/inventory/units/{id}/`
- DELETE `/api/inventory/units/{id}/`

### Products
- GET `/api/inventory/products/`
- POST `/api/inventory/products/`
- GET `/api/inventory/products/{id}/`
- PATCH `/api/inventory/products/{id}/`
- DELETE `/api/inventory/products/{id}/`

### Warehouses
- GET `/api/inventory/warehouses/`
- POST `/api/inventory/warehouses/`
- GET `/api/inventory/warehouses/{id}/`
- PATCH `/api/inventory/warehouses/{id}/`
- DELETE `/api/inventory/warehouses/{id}/`

### Stock Transactions
- GET `/api/inventory/stock-transactions/`
- POST `/api/inventory/stock-transactions/`
- GET `/api/inventory/stock-transactions/{id}/`
- PATCH `/api/inventory/stock-transactions/{id}/`
- DELETE `/api/inventory/stock-transactions/{id}/`
- POST `/api/inventory/stock-transactions/{id}/post/`

### Stock Movements
- GET `/api/inventory/stock-movements/`
- POST `/api/inventory/stock-movements/`
- GET `/api/inventory/stock-movements/{id}/`
- PATCH `/api/inventory/stock-movements/{id}/`
- DELETE `/api/inventory/stock-movements/{id}/`

### Stock Balances
- GET `/api/inventory/stock-balances/`
- GET `/api/inventory/stock-balances/{id}/`

---

## Sales

### Sales Invoices
- GET `/api/sales/invoices/`
- POST `/api/sales/invoices/`
- GET `/api/sales/invoices/{id}/`
- PATCH `/api/sales/invoices/{id}/`
- DELETE `/api/sales/invoices/{id}/`
- POST `/api/sales/invoices/{id}/post/`

### Sales Invoice Items
- GET `/api/sales/invoice-items/`
- POST `/api/sales/invoice-items/`
- GET `/api/sales/invoice-items/{id}/`
- PATCH `/api/sales/invoice-items/{id}/`
- DELETE `/api/sales/invoice-items/{id}/`

---

## Purchases

### Purchase Invoices
- GET `/api/purchases/invoices/`
- POST `/api/purchases/invoices/`
- GET `/api/purchases/invoices/{id}/`
- PATCH `/api/purchases/invoices/{id}/`
- DELETE `/api/purchases/invoices/{id}/`
- POST `/api/purchases/invoices/{id}/post/`

### Purchase Invoice Items
- GET `/api/purchases/invoice-items/`
- POST `/api/purchases/invoice-items/`
- GET `/api/purchases/invoice-items/{id}/`
- PATCH `/api/purchases/invoice-items/{id}/`
- DELETE `/api/purchases/invoice-items/{id}/`

---

## API Documentation
- GET `/api/schema/`
- GET `/api/docs/`
- GET `/api/redoc/`

---

## Posting Flows

### Sales
- Create sales invoice
- Add invoice items
- Post sales invoice
- Posting may create stock OUT transactions

### Purchases
- Create purchase invoice
- Add invoice items
- Post purchase invoice
- Posting may create stock IN transactions

### Inventory
- Create stock transaction
- Add stock movements
- Post stock transaction
- Posting updates stock balances

---

## Status Rules
- `draft` → editable
- `posted` → read-only
- `cancelled` → inactive / closed document state

---

## Deferred for Later Phases
- Accounting APIs
- Cancel / reverse document flows
- Additional reporting endpoints
- Dashboard APIs
- Advanced lookups
- Automated API tests