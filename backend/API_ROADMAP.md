# API Roadmap - ERP V1

## Auth
- POST /api/auth/login/
- POST /api/auth/refresh/
- GET /api/auth/me/
- GET /api/auth/context/

## Partners
- GET /api/partners/partners/
- POST /api/partners/partners/
- GET /api/partners/partners/{id}/
- PATCH /api/partners/partners/{id}/
- GET /api/partners/partners/customers/
- GET /api/partners/partners/suppliers/

## Inventory - Units
- GET /api/inventory/units/
- POST /api/inventory/units/
- GET /api/inventory/units/{id}/
- PATCH /api/inventory/units/{id}/

## Inventory - Products
- GET /api/inventory/products/
- POST /api/inventory/products/
- GET /api/inventory/products/{id}/
- PATCH /api/inventory/products/{id}/

## Inventory - Warehouses
- GET /api/inventory/warehouses/
- POST /api/inventory/warehouses/
- GET /api/inventory/warehouses/{id}/
- PATCH /api/inventory/warehouses/{id}/

## Inventory - Stock Transactions
- GET /api/inventory/stock-transactions/
- POST /api/inventory/stock-transactions/
- GET /api/inventory/stock-transactions/{id}/
- PATCH /api/inventory/stock-transactions/{id}/
- DELETE /api/inventory/stock-transactions/{id}/
- POST /api/inventory/stock-transactions/{id}/post/

## Inventory - Stock Movements
- GET /api/inventory/stock-movements/
- POST /api/inventory/stock-movements/
- GET /api/inventory/stock-movements/{id}/
- PATCH /api/inventory/stock-movements/{id}/
- DELETE /api/inventory/stock-movements/{id}/

## Inventory - Stock Balances
- GET /api/inventory/stock-balances/
- GET /api/inventory/stock-balances/{id}/

## Sales Invoices
- GET /api/sales/invoices/
- POST /api/sales/invoices/
- GET /api/sales/invoices/{id}/
- PATCH /api/sales/invoices/{id}/
- DELETE /api/sales/invoices/{id}/
- POST /api/sales/invoices/{id}/post/

## Sales Invoice Items
- GET /api/sales/invoice-items/
- POST /api/sales/invoice-items/
- GET /api/sales/invoice-items/{id}/
- PATCH /api/sales/invoice-items/{id}/
- DELETE /api/sales/invoice-items/{id}/

## Purchases Invoices
- GET /api/purchases/invoices/
- POST /api/purchases/invoices/
- GET /api/purchases/invoices/{id}/
- PATCH /api/purchases/invoices/{id}/
- DELETE /api/purchases/invoices/{id}/
- POST /api/purchases/invoices/{id}/post/

## Purchases Invoice Items
- GET /api/purchases/invoice-items/
- POST /api/purchases/invoice-items/
- GET /api/purchases/invoice-items/{id}/
- PATCH /api/purchases/invoice-items/{id}/
- DELETE /api/purchases/invoice-items/{id}/

## Docs
- GET /api/schema/
- GET /api/docs/
- GET /api/redoc/