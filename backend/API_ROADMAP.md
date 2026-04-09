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

## Sales Invoices
- GET /api/sales/invoices/
- POST /api/sales/invoices/
- GET /api/sales/invoices/{id}/
- PATCH /api/sales/invoices/{id}/
- POST /api/sales/invoices/{id}/post/

## Sales Invoice Items
- GET /api/sales/invoice-items/
- POST /api/sales/invoice-items/
- GET /api/sales/invoice-items/{id}/
- PATCH /api/sales/invoice-items/{id}/
- DELETE /api/sales/invoice-items/{id}/