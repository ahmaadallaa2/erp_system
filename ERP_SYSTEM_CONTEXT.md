# ERP System Context

Master handover document for the `ERP_SYSTEM` project.

This document is written for a senior AI/software architect assistant that needs to understand the repository without re-reading the full codebase. It documents the actual implementation found in the project, including architecture, models, services, APIs, frontend structure, current status, limitations, and likely roadmap.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Tech Stack](#tech-stack)
4. [High-Level Architecture](#high-level-architecture)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [Apps and Modules](#apps-and-modules)
8. [Database Design](#database-design)
9. [Core Business Workflows](#core-business-workflows)
10. [API and Views](#api-and-views)
11. [Authentication and Permissions](#authentication-and-permissions)
12. [Accounting Implementation](#accounting-implementation)
13. [Inventory and Warehouse Implementation](#inventory-and-warehouse-implementation)
14. [AI Document Assistant](#ai-document-assistant)
15. [Reports and Dashboard](#reports-and-dashboard)
16. [Important Technical Decisions](#important-technical-decisions)
17. [Important Files and Responsibilities](#important-files-and-responsibilities)
18. [Tests](#tests)
19. [Current Implementation Status](#current-implementation-status)
20. [Known Problems and Limitations](#known-problems-and-limitations)
21. [Scalability Concerns](#scalability-concerns)
22. [Future Roadmap](#future-roadmap)
23. [Developer Notes](#developer-notes)
24. [Summary for Next Assistant](#summary-for-next-assistant)

---

## Project Overview

This repository contains a Django-based ERP system with a React/Vite frontend. The project implements core operational ERP modules for:

- Companies and branches
- Users and JWT authentication
- Partners, meaning customers, suppliers, or partners that can act as both
- Inventory products, units, categories, warehouses, stock balances, and stock movements
- Purchase invoices
- Sales invoices
- Accounting accounts, journals, entries, journal items, and payments
- AI document assistant for PDF/DOCX upload, RAG processing, semantic search, and question answering

The backend is the primary source of business truth. The frontend is a lightweight operational interface that consumes the REST API.

The system is designed as a modular Django monolith. Each ERP domain has its own Django app, and domain workflows are mostly implemented through service classes rather than directly inside API views.

---

## Repository Structure

Top-level repository:

```text
erp_system/
├── README.md
├── ERP_SYSTEM_CONTEXT.md
├── backend/
│   ├── API_ROADMAP.md
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── accounting/
│   │   ├── ai_assistant/
│   │   ├── core/
│   │   ├── inventory/
│   │   ├── partners/
│   │   ├── purchases/
│   │   ├── sales/
│   │   └── users/
│   └── templates/
│       ├── 403.html
│       ├── base.html
│       ├── parts/
│       └── users/
└── frontend/
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── vite.config.ts
    ├── tsconfig*.json
    ├── eslint.config.js
    ├── public/
    └── src/
        ├── App.tsx
        ├── main.tsx
        ├── app/
        ├── components/
        ├── features/
        ├── lib/
        ├── pages/
        └── styles/
```

Backend app layout pattern:

```text
backend/apps/{app_name}/
├── admin/
├── api/
│   ├── serializers.py or serializers/
│   ├── urls.py
│   └── views.py or views/
├── migrations/
├── models/
├── services/
├── tests/
├── apps.py
└── __init__.py
```

Not every app has every folder. For example, `accounting/api` exists but is currently empty/not mounted.

Frontend feature layout pattern:

```text
frontend/src/features/{feature}/
├── api/
├── pages/
└── types/
```

---

## Tech Stack

### Backend

Declared in `backend/requirements.txt`:

- Django `6.0.2`
- Django REST Framework `3.16.1`
- PostgreSQL through `psycopg2-binary`
- SimpleJWT through `djangorestframework_simplejwt`
- drf-spectacular for OpenAPI, Swagger, ReDoc
- django-cors-headers
- django-filter
- django-unfold for Django admin UI
- django-extensions
- python-dotenv
- Pillow
- pypdf
- python-docx
- sentence-transformers
- faiss-cpu
- langchain
- langchain-community
- langchain-ollama
- ollama

### Frontend

Declared in `frontend/package.json`:

- React `19.2.4`
- React DOM `19.2.4`
- TypeScript `~6.0.2`
- Vite `8.0.4`
- React Router `7.14.0`
- Axios `1.15.0`
- Zustand `5.0.12`
- react-hot-toast
- ESLint

### Database

Configured in `backend/config/settings.py`:

- PostgreSQL database engine
- Environment variables:
  - `DB_NAME`, default `erp_db`
  - `DB_USER`, default `postgres`
  - `DB_PASSWORD`, default empty string
  - `DB_HOST`, default `localhost`
  - `DB_PORT`, default `5432`

### API Docs

Configured with drf-spectacular:

- `GET /api/schema/`
- `GET /api/docs/`
- `GET /api/redoc/`

---

## High-Level Architecture

### System Diagram

```text
                          ┌──────────────────────────────┐
                          │        React Frontend         │
                          │  Vite + TypeScript + Axios    │
                          └───────────────┬──────────────┘
                                          │
                                          │ HTTP JSON / multipart
                                          │ Bearer JWT
                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Django Backend                              │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐            │
│  │  users   │ │ partners │ │ inventory │ │ purchases  │            │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └─────┬──────┘            │
│       │            │             │             │                   │
│  ┌────▼────┐ ┌─────▼─────┐ ┌─────▼──────┐ ┌────▼─────────┐         │
│  │  core   │ │   sales   │ │ accounting │ │ ai_assistant │         │
│  └─────────┘ └───────────┘ └────────────┘ └──────────────┘         │
│                                                                     │
│  DRF ViewSets → Serializers → Models → Services → Database          │
│                                                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
                      ┌────────────────────┐
                      │     PostgreSQL      │
                      └────────────────────┘

AI assistant also writes uploaded files and FAISS indexes under MEDIA_ROOT.
```

### Backend Flow Pattern

```text
Request
  ↓
DRF ViewSet / APIView
  ↓
Serializer validation
  ↓
Model validation and persistence
  ↓
Service class for posting/business workflow
  ↓
Database changes inside transaction.atomic()
  ↓
Response
```

### Posting Pattern

Most operational documents follow:

```text
draft
  ├── editable
  ├── can add/delete line items
  └── can be posted

posted
  ├── read-only
  ├── stock/accounting side effects have occurred
  └── cannot be normally edited

cancelled
  ├── status exists
  └── full reversal/cancellation workflow is not implemented yet
```

---

## Backend Architecture

Main backend configuration:

- `backend/config/settings.py`
- `backend/config/urls.py`
- `backend/config/asgi.py`
- `backend/config/wsgi.py`

`settings.py` inserts `BASE_DIR / "apps"` into `sys.path`, but installed apps are still referenced as `apps.core`, `apps.users`, etc.

Installed project apps:

```python
'apps.core',
'apps.users',
'apps.inventory',
'apps.partners',
'apps.purchases',
'apps.accounting',
'apps.sales',
'apps.ai_assistant',
```

Third-party apps include:

```python
'rest_framework',
'corsheaders',
'rest_framework_simplejwt',
'drf_spectacular',
'django_filters',
'unfold',
```

### REST Framework Settings

Configured in `backend/config/settings.py`:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
```

This means API endpoints are authenticated by default unless overridden.

### JWT Settings

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

### CORS

Only the Vite dev origin is allowed:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True
```

### Middleware

Notable middleware:

- `corsheaders.middleware.CorsMiddleware`
- `django.contrib.auth.middleware.LoginRequiredMiddleware`
- `apps.core.middleware.ThreadLocalMiddleware`

Important warning: `LoginRequiredMiddleware` can affect API behavior if not carefully handled, potentially returning login redirects rather than JSON authentication errors.

### URL Mounts

Defined in `backend/config/urls.py`:

```text
/admin/
/api/auth/
/api/partners/
/api/inventory/
/api/sales/
/api/purchases/
/api/ai-assistant/
/api/schema/
/api/docs/
/api/redoc/
```

Important: `apps.accounting.api` exists, but accounting APIs are not mounted in `config/urls.py`.

---

## Frontend Architecture

Main frontend files:

- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/app/layouts/AppLayout.tsx`
- `frontend/src/app/routes/ProtectedRoute.tsx`
- `frontend/src/app/store/auth-store.ts`
- `frontend/src/lib/api/axios.ts`
- `frontend/src/lib/api/endpoints.ts`

### Routing

Routes in `frontend/src/App.tsx`:

```text
/login
/dashboard
/partners
/products
/warehouses
/stock-transactions
/stock-balances
/stock-movements
/purchase-invoices
/purchase-invoices/new
/purchase-invoices/:id
/sales-invoices
/sales-invoices/new
/sales-invoices/:id
/ai-assistant
```

Protected routes are wrapped by `ProtectedRoute`, which checks Zustand state:

```ts
const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
```

### Axios Client

Defined in `frontend/src/lib/api/axios.ts`.

Current base URL:

```ts
baseURL: "http://127.0.0.1:9000/api"
```

Request interceptor adds:

```text
Authorization: Bearer {accessToken}
```

Important limitations:

- API URL is hardcoded.
- There is no automatic token refresh.
- Expired access tokens likely require logging in again.

### State Management

`frontend/src/app/store/auth-store.ts` uses Zustand with persistence. It stores:

- `accessToken`
- `refreshToken`
- `isAuthenticated`

Methods:

- `setTokens(access, refresh)`
- `logout()`

### Frontend Feature Modules

Important feature folders:

```text
frontend/src/features/ai-assistant/
frontend/src/features/dashboard/
frontend/src/features/partners/
frontend/src/features/products/
frontend/src/features/purchase-invoices/
frontend/src/features/sales-invoices/
frontend/src/features/stock-balances/
frontend/src/features/stock-movements/
frontend/src/features/stock-transactions/
frontend/src/features/warehouses/
```

Most frontend pages are simple data tables or form/detail pages using inline React styles.

Accounting has no frontend feature screens.

---

## Apps and Modules

## `apps.core`

Responsibilities:

- Shared base models
- Soft deletion
- Audit logging
- Companies and branches
- Fiscal years
- System settings singleton
- Generic attachments
- Atomic sequence generation
- Thread-local current-user tracking

Important files:

```text
backend/apps/core/models/base.py
backend/apps/core/models/company.py
backend/apps/core/models/sequences.py
backend/apps/core/models/fisical_year.py
backend/apps/core/models/system_settings.py
backend/apps/core/models/audit.py
backend/apps/core/models/attachments.py
backend/apps/core/middleware.py
backend/apps/core/managers.py
backend/apps/core/signals.py
backend/apps/core/admin/
```

### `BaseModel`

Defined in `backend/apps/core/models/base.py`.

Fields:

- `id`: UUID primary key
- `created_at`
- `updated_at`
- `created_by`
- `updated_by`

Behavior:

- Captures original field state during initialization.
- Uses `get_current_user()` from `apps.core.middleware`.
- Fills `created_by` and `updated_by` automatically when a request user exists.
- Writes `AuditLog` rows for create and update.

### `SoftDeleteModel`

Defined in `backend/apps/core/models/base.py`.

Extends `BaseModel`.

Fields:

- `is_deleted`
- `deleted_at`
- `deleted_by`

Managers:

- `objects = SoftDeleteManager()`
- `all_objects = models.Manager()`

Behavior:

- Overrides `delete()` to soft-delete.
- `soft_delete()` marks deletion fields and writes audit delete action.
- `restore()` clears deletion fields and writes audit restore action.

### `SoftDeleteManager`

Defined in `backend/apps/core/managers.py`.

Behavior:

```python
return super().get_queryset().filter(is_deleted=False)
```

This means default model queries hide soft-deleted records.

### `AuditLog`

Defined in `backend/apps/core/models/audit.py`.

Fields:

- `user`
- `action`: `create`, `update`, `delete`, `restore`
- `content_type`
- `object_id`
- `content_object`
- `changes`
- `timestamp`
- `ip_address`
- `browser_info`

Purpose:

- Generic audit trail for model changes.

Current limitation:

- `ip_address` and `browser_info` fields exist but are not populated by the current helper.

### `Sequence`

Defined in `backend/apps/core/models/sequences.py`.

Fields:

- `key`
- `prefix`
- `current_value`
- `padding`

Important method:

```python
Sequence.next_number(key, prefix="DOC-", padding=5)
```

Implementation:

- Uses `transaction.atomic()`
- Uses `select_for_update()`
- Handles race condition on first create with `IntegrityError`

Used for:

- Branch codes
- Partner codes
- Product SKUs
- Warehouse codes
- Stock transaction codes
- Sales invoice numbers
- Purchase invoice numbers
- Journal entry numbers
- Payment voucher numbers

### `Company`

Defined in `backend/apps/core/models/company.py`.

Fields:

- `name`
- `logo`
- `tax_number`
- `commercial_record`
- `email`
- `phone`
- `website`
- `address`

### `Branch`

Defined in `backend/apps/core/models/company.py`.

Fields:

- `company`
- `name`
- `code`
- `address`
- `phone`
- `is_active`

Behavior:

- Auto-generates `code` if missing.
- Sequence key: `branch_code_comp_{company_id}`
- Prefix: `BR-`
- Padding: `3`
- Unique active branch code per company through a conditional unique constraint.

### `FiscalYear`

Defined in `backend/apps/core/models/fisical_year.py`.

Fields:

- `company`
- `name`
- `start_date`
- `end_date`
- `is_active`
- `is_closed`

Validation:

- Start date must be before or equal to end date.
- Only one active fiscal year per company.

Important note:

- The file is named `fisical_year.py`, not `fiscal_year.py`.

### `SystemSetting`

Defined in `backend/apps/core/models/system_settings.py`.

Fields:

- `system_name`
- `is_maintenance_mode`
- `allow_registration`
- `default_currency`
- `default_vat_percentage`
- `decimal_places`
- `session_timeout_minutes`

Behavior:

- Singleton-like model.
- Prevents creating more than one settings row.
- Cached under key `core_system_settings`.
- `get_settings()` creates a default row if none exists.

### `Attachment`

Defined in `backend/apps/core/models/attachments.py`.

Generic attachment model using Django contenttypes.

Fields:

- `content_type`
- `object_id`
- `content_object`
- `file`
- `name`
- `note`
- `file_type`

Upload path:

```text
attachments/{model_name}/{object_id}/{uuid}.{ext}
```

Behavior:

- Automatically fills display name from filename if missing.
- Extracts file extension.
- Deletes old physical file if a replacement file is uploaded.
- `apps.core.signals.auto_delete_file_on_delete` deletes physical file after attachment deletion.

### `ThreadLocalMiddleware`

Defined in `backend/apps/core/middleware.py`.

Purpose:

- Stores `request.user` in thread-local storage so models can access the current user indirectly.
- Used by `BaseModel` audit fields.

---

## `apps.users`

Responsibilities:

- Custom email-based user model
- User company/branch assignment
- JWT auth API
- Role/group helper definitions
- Role setup management command
- Template login page

Important files:

```text
backend/apps/users/models/user.py
backend/apps/users/managers.py
backend/apps/users/roles.py
backend/apps/users/api/serializers.py
backend/apps/users/api/views.py
backend/apps/users/api/urls.py
backend/apps/users/management/commands/setup_roles.py
backend/apps/users/views.py
backend/templates/users/login.html
```

### `User`

Defined in `backend/apps/users/models/user.py`.

Extends Django `AbstractUser`.

Important implementation:

- UUID primary key.
- `username = None`
- `email` is unique.
- `USERNAME_FIELD = "email"`
- `REQUIRED_FIELDS = ["full_name"]`
- Uses `CustomUserManager`.

Fields:

- `email`
- `full_name`
- `phone`
- `job_title`
- `user_type`
- `company`
- `branch`

User types:

```text
system_admin
company_admin
branch_manager
employee
```

Validation:

- Branch must belong to selected company.
- If branch is selected and company is missing, company is inferred from branch.
- `company_admin` requires company.
- `branch_manager` requires company and branch.

Soft-delete behavior:

- User does not inherit `SoftDeleteModel`.
- `soft_delete()` simply sets `is_active=False`.

### `CustomUserManager`

Defined in `backend/apps/users/managers.py`.

Important methods:

- `create_user(email, password=None, **extra_fields)`
- `create_superuser(email, password=None, **extra_fields)`

It normalizes email and properly hashes passwords.

### Roles

Defined in `backend/apps/users/roles.py`.

Role/group constants:

- `GROUP_SUPER_ADMIN`
- `GROUP_MANAGER`
- `GROUP_ACCOUNTANT`
- `GROUP_INVENTORY`
- `GROUP_SALES`

Helper functions:

- `is_in_group(user, group_name)`
- `has_object_permission(user, obj, permission_type="view")`
- `create_default_groups()`

Object permission behavior is currently minimal:

- Superusers pass.
- Record creators pass if the object has `created_by`.
- No deeper branch/company manager logic is implemented.

### `setup_roles` Command

File:

```text
backend/apps/users/management/commands/setup_roles.py
```

Purpose:

- Creates default groups.
- Assigns model permissions to groups.

Important issues:

- It imports from `backend.apps.users.roles`, while the rest of the project generally uses `apps.users.roles`.
- Some permission codenames appear outdated/mismatched:
  - `view_customer`
  - `add_customer`
  - `view_supplier`
  - `view_inventorymovement`

Actual models are `Partner`, `StockTransaction`, and `StockMovement`, so this command likely needs correction before production use.

### Users API

Routes in `backend/apps/users/api/urls.py`:

```text
POST /api/auth/login/
POST /api/auth/refresh/
GET  /api/auth/me/
GET  /api/auth/context/
```

Views:

- `LoginAPIView`
- `RefreshAPIView`
- `MeAPIView`
- `ContextAPIView`

`CustomTokenObtainPairSerializer` adds JWT claims:

- `user_id`
- `email`
- `company_id`
- `branch_id`

Login response includes a `user` object:

```json
{
  "id": "...",
  "email": "...",
  "full_name": "...",
  "user_type": "...",
  "company_id": "...",
  "branch_id": "..."
}
```

---

## `apps.partners`

Responsibilities:

- Customer records
- Supplier records
- Dual customer/supplier partner records
- Partner balances from journal items
- Partner API with customer/supplier lookup actions

Important files:

```text
backend/apps/partners/models/partner.py
backend/apps/partners/api/serializers.py
backend/apps/partners/api/views.py
backend/apps/partners/api/urls.py
backend/apps/partners/admin/partners_admin.py
```

### `Partner`

Defined in `backend/apps/partners/models/partner.py`.

Extends `SoftDeleteModel`.

Fields:

- `company`
- `code`
- `partner_type`
- `name`
- `phone`
- `mobile`
- `email`
- `website`
- `address`
- `city`
- `tax_number`
- `commercial_record`
- `credit_limit`
- `initial_balance`
- `is_active`
- `notes`
- `responsible`

Partner types:

```text
customer
supplier
both
```

Code generation:

```text
customer -> CUST- / customer_code_comp_{company_id}
supplier -> SUP-  / supplier_code_comp_{company_id}
both     -> PRT-  / partner_code_both_comp_{company_id}
```

Constraint:

- Unique active partner code per company.

Computed property:

```python
current_balance
```

Uses posted `JournalItem` rows:

```text
Customer: initial_balance + debit - credit
Supplier/Both: initial_balance + credit - debit
```

### Partners API

Router prefix:

```text
/api/partners/partners/
```

Endpoints:

```text
GET    /api/partners/partners/
POST   /api/partners/partners/
GET    /api/partners/partners/{id}/
PATCH  /api/partners/partners/{id}/
DELETE /api/partners/partners/{id}/
GET    /api/partners/partners/customers/
GET    /api/partners/partners/suppliers/
```

Filtering:

- `partner_type`
- `search`

Querysets are scoped to `request.user.company`.

---

## `apps.inventory`

Responsibilities:

- Product categories
- Units of measure
- Product master data
- Warehouses
- Stock transaction headers
- Stock movement lines
- Current stock balances
- Inventory posting logic

Important files:

```text
backend/apps/inventory/models/category.py
backend/apps/inventory/models/unit.py
backend/apps/inventory/models/product.py
backend/apps/inventory/models/warehouse.py
backend/apps/inventory/models/stock_transaction.py
backend/apps/inventory/models/stock_movement.py
backend/apps/inventory/models/stock_balance.py
backend/apps/inventory/services/stock_service.py
backend/apps/inventory/api/serializers/
backend/apps/inventory/api/views/
backend/apps/inventory/api/urls.py
backend/apps/inventory/admin.py
backend/apps/inventory/tests/test_stock_service.py
```

### `Category`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `name`
- `parent`
- `description`
- `is_active`
- `icon`

Behavior:

- Tree structure via self-referencing `parent`.
- Parent cannot be itself.
- Parent must belong to same company.
- Unique active category name per parent per company.

### `Unit`

Extends `SoftDeleteModel`.

Fields:

- `name`
- `short_name`
- `is_active`

Constraints:

- Unique active unit name.
- Unique active unit short name.

Important note:

- Units are global, not company-scoped.

### `Product`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `category`
- `unit`
- `name`
- `sku`
- `barcode`
- `product_type`
- `image`
- `description`
- `cost_price`
- `average_cost`
- `sale_price`
- `reorder_point`
- `income_account`
- `expense_account`
- `is_active`

Product types:

```text
storable
service
consumable
```

Behavior:

- Auto-generates SKU:
  - Prefix: `PROD-`
  - Sequence key: `product_sku_comp_{company_id}`
  - Padding: `6`
- Category must belong to same company.
- Income/expense accounts must belong to same company if account has company ID.
- Unique active SKU per company.

Upload path:

```text
company_{company_id}/products/{uuid}.{ext}
```

Important business rule:

- Service products cannot create stock movements.

### `Warehouse`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `name`
- `code`
- `warehouse_type`
- `branch`
- `keeper`
- `address`
- `is_active`

Warehouse types:

```text
main
sub
```

Behavior:

- Auto-generates code:
  - Prefix: `WH-`
  - Sequence key: `warehouse_code_comp_{company_id}`
  - Padding: `4`
- Branch must belong to same company.
- Keeper must belong to same company if keeper has company.

Constraints:

- Unique active warehouse name per branch.
- Unique active warehouse code per company.

### `StockTransaction`

Extends `BaseModel`.

Fields:

- `company`
- `code`
- `transaction_type`
- `source_warehouse`
- `destination_warehouse`
- `date`
- `status`
- `reference`
- `notes`
- `journal_entry`

Transaction types:

```text
IN
OUT
TRANSFER
```

Status choices:

```text
draft
posted
cancelled
```

Code generation:

```text
IN       -> IN-  / stock_in_comp_{company_id}
OUT      -> OUT- / stock_out_comp_{company_id}
TRANSFER -> TRF- / stock_transfer_comp_{company_id}
```

Validation:

- Source warehouse must belong to company.
- Destination warehouse must belong to company if present.
- `TRANSFER` requires destination warehouse.
- `TRANSFER` cannot have same source and destination.
- Non-transfer transactions cannot have destination warehouse.

Properties:

- `total_items`
- `can_edit`
- `can_post`
- `can_cancel`

Important naming note:

- For `IN` transactions, `source_warehouse` is used as the receiving warehouse. This works technically but is semantically confusing.

### `StockMovement`

Extends `BaseModel`.

Fields:

- `transaction`
- `product`
- `quantity`
- `unit_cost`
- `note`

Validation:

- Quantity must be greater than zero.
- Unit cost cannot be negative.
- Product must belong to transaction company.
- Service products cannot create stock movements.
- Cannot edit/delete movement after parent transaction is posted.

### `StockBalance`

Extends `BaseModel`.

Fields:

- `company`
- `product`
- `warehouse`
- `quantity`
- `reserved_quantity`
- `location`
- `reorder_point`

Constraint:

- Unique company/product/warehouse.

Computed property:

```python
available_quantity = quantity - reserved_quantity
```

Validation:

- Product must belong to same company.
- Warehouse must belong to same company.
- If company is missing and warehouse exists, company is inferred from warehouse.

### `StockService`

Defined in `backend/apps/inventory/services/stock_service.py`.

Methods:

```python
StockService.post_transaction(transaction_obj)
StockService.create_movement(transaction_obj, product, quantity, unit_cost=None, note=None)
```

`post_transaction`:

- Requires transaction status to be `draft`.
- Rejects empty transactions.
- Uses `transaction.atomic`.
- Uses `select_for_update()` on stock balance rows.
- Handles IN, OUT, and TRANSFER.
- Sets transaction status to `posted`.

IN behavior:

- Creates/locks stock balance.
- Increases quantity.
- Updates weighted average cost if unit cost is positive.

OUT behavior:

- Creates/locks stock balance.
- Calculates available quantity as quantity minus reserved.
- Rejects insufficient stock.
- Decreases quantity.

TRANSFER behavior:

- Requires destination warehouse.
- Locks source and destination balances.
- Rejects insufficient source stock.
- Decreases source quantity.
- Increases destination quantity.

Weighted average cost method:

```python
_update_average_cost_on_in(product, incoming_qty, incoming_unit_cost)
```

It calculates total quantity across product/company balances and updates `product.average_cost`.

### Inventory API

Routes:

```text
/api/inventory/units/
/api/inventory/products/
/api/inventory/warehouses/
/api/inventory/stock-transactions/
/api/inventory/stock-movements/
/api/inventory/stock-balances/
```

Posting endpoint:

```text
POST /api/inventory/stock-transactions/{id}/post/
```

Filters:

- Products: `product_type`, `category`, `search`
- Warehouses: `branch`, `warehouse_type`, `search`
- Stock transactions: `type`, `status`
- Stock movements: `transaction`
- Stock balances: `product`, `warehouse`, `search`, `low_stock`

Company scoping:

- Most inventory querysets filter by `request.user.company`.
- Units are global.

---

## `apps.purchases`

Responsibilities:

- Purchase invoice headers
- Purchase invoice line items
- Purchase invoice posting into inventory

Important files:

```text
backend/apps/purchases/models/purchase_invoice.py
backend/apps/purchases/models/purchase_invoice_item.py
backend/apps/purchases/services/purchase_service.py
backend/apps/purchases/api/serializers/invoices.py
backend/apps/purchases/api/views/invoices.py
backend/apps/purchases/api/urls.py
backend/apps/purchases/admin/purchase_invoice_admin.py
backend/apps/purchases/tests/test_purchase_service.py
```

### `PurchaseInvoice`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `invoice_number`
- `branch`
- `supplier`
- `warehouse`
- `status`
- `invoice_date`
- `vendor_bill_number`
- `total_amount`
- `shipping_cost`
- `clearance_cost`
- `commission_percentage`
- `notes`

Status choices:

```text
draft
posted
cancelled
```

Behavior:

- Auto-generates invoice number:
  - Prefix: `PINV-`
  - Sequence key: `pinv_branch_{branch_id}`
  - Padding: `5`
- Supplier must be a partner of type `supplier` or `both`.
- Branch, supplier, and warehouse must belong to same company.
- Unique active invoice number per branch.

### `PurchaseInvoiceItem`

Extends `BaseModel`.

Fields:

- `invoice`
- `product`
- `quantity`
- `unit_price`
- `line_total`
- `notes`

Behavior:

- Quantity must be greater than zero.
- Unit price cannot be negative.
- Product must belong to invoice company.
- Cannot update/delete item after invoice is posted.
- Calculates `line_total = quantity * unit_price`, rounded to 2 decimals.
- Recalculates invoice total after save/delete.

Invoice total formula:

```text
sum(item.line_total) + shipping_cost + clearance_cost
```

Important limitation:

- `commission_percentage` is not included in invoice total recalculation, although accounting service uses commission when creating purchase accounting entries.

### `PurchaseService`

Defined in `backend/apps/purchases/services/purchase_service.py`.

Method:

```python
PurchaseService.post_invoice(invoice)
```

Behavior:

- Requires invoice status `draft`.
- Rejects empty invoices.
- Creates `StockTransaction` with `transaction_type="IN"`.
- Uses invoice warehouse as `source_warehouse`.
- Creates a stock movement for each item.
- Movement `unit_cost` equals purchase item `unit_price`.
- Calls `StockService.post_transaction(stock_tx)`.
- Sets invoice status to `posted`.
- Returns created stock transaction.

Important limitation:

- Does not create accounting journal entries.
- Does not link a journal entry to the invoice.

### Purchases API

Routes:

```text
GET/POST      /api/purchases/invoices/
GET/PATCH/DEL /api/purchases/invoices/{id}/
POST          /api/purchases/invoices/{id}/post/

GET/POST      /api/purchases/invoice-items/
GET/PATCH/DEL /api/purchases/invoice-items/{id}/
```

Invoice filters:

- `status`
- `supplier`
- `warehouse`
- `date_from`
- `date_to`

Create behavior:

- Requires authenticated user to have company and branch.
- Saves invoice with user company and branch.

Update/delete behavior:

- Only draft invoices/items can be updated or deleted.

---

## `apps.sales`

Responsibilities:

- Sales invoice headers
- Sales invoice line items
- Sales invoice posting into inventory

Important files:

```text
backend/apps/sales/models/sales_invoice.py
backend/apps/sales/models/sales_invoice_item.py
backend/apps/sales/services/sales_service.py
backend/apps/sales/api/serializers/invoices.py
backend/apps/sales/api/views/invoices.py
backend/apps/sales/api/urls.py
backend/apps/sales/admin.py
backend/apps/sales/tests/test_sales_service.py
```

### `SalesInvoice`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `branch`
- `invoice_number`
- `customer`
- `warehouse`
- `date`
- `status`
- `total_amount`
- `notes`

Status choices:

```text
draft
posted
cancelled
```

Behavior:

- Auto-generates invoice number:
  - Prefix: `SINV-`
  - Sequence key: `sinv_branch_{branch_id}`
  - Padding: `5`
- Customer must be a partner of type `customer` or `both`.
- Branch, customer, and warehouse must belong to same company.
- Unique active invoice number per branch.

### `SalesInvoiceItem`

Extends `BaseModel`.

Fields:

- `invoice`
- `product`
- `quantity`
- `unit_price`
- `line_total`
- `notes`

Behavior:

- Quantity must be greater than zero.
- Unit price cannot be negative.
- Product must belong to invoice company.
- Cannot update/delete item after invoice is posted.
- Calculates `line_total = quantity * unit_price`, rounded to 2 decimals.
- Recalculates invoice total after save/delete.

Invoice total formula:

```text
sum(item.line_total)
```

### `SalesService`

Defined in `backend/apps/sales/services/sales_service.py`.

Method:

```python
SalesService.post_invoice(invoice)
```

Behavior:

- Requires invoice status `draft`.
- Rejects empty invoices.
- Requires total amount > 0.
- Filters stock items where `product.product_type != "service"`.
- If stock items exist, invoice warehouse is required.
- Creates `StockTransaction` with `transaction_type="OUT"`.
- Creates stock movements for stock items.
- Movement `unit_cost` uses `product.average_cost`.
- Calls `StockService.post_transaction(stock_tx)`.
- Sets invoice status to `posted`.
- Returns the invoice.

Important limitations:

- Does not create accounting journal entries.
- Does not link a journal entry to the invoice.
- Does not create COGS accounting.

Important test mismatch:

- `backend/apps/sales/tests/test_sales_service.py` expects `SalesService.post_invoice()` to return a stock transaction or `None`.
- Current implementation returns the invoice.

### Sales API

Routes:

```text
GET/POST      /api/sales/invoices/
GET/PATCH/DEL /api/sales/invoices/{id}/
POST          /api/sales/invoices/{id}/post/

GET/POST      /api/sales/invoice-items/
GET/PATCH/DEL /api/sales/invoice-items/{id}/
```

Invoice filters:

- `status`
- `customer`
- `date_from`
- `date_to`

Create behavior:

- Requires authenticated user to have company and branch.
- Saves invoice with user company and branch.

Update/delete behavior:

- Only draft invoices/items can be updated or deleted.

---

## `apps.accounting`

Responsibilities:

- Chart of accounts
- Journals
- Journal entries
- Journal items
- Payments
- Accounting service logic for invoices and payments

Important files:

```text
backend/apps/accounting/models/account.py
backend/apps/accounting/models/journal.py
backend/apps/accounting/models/entry.py
backend/apps/accounting/models/payment.py
backend/apps/accounting/services/accounting_service.py
backend/apps/accounting/services/payment_service.py
backend/apps/accounting/admin/
backend/apps/accounting/tests/
```

Current exposure:

- Accounting models are available in Django admin.
- Accounting services and tests exist.
- Accounting REST APIs are not mounted.

### `Account`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `code`
- `name`
- `parent`
- `account_type`
- `normal_balance`
- `is_postable`
- `allow_reconciliation`
- `is_active`

Account types:

```text
asset
liability
equity
income
expense
```

Normal balance:

```text
debit
credit
```

Natural balance map:

```python
{
    "asset": "debit",
    "expense": "debit",
    "liability": "credit",
    "equity": "credit",
    "income": "credit",
}
```

Validation:

- Parent cannot be itself.
- Parent must belong to same company.
- Child account type must match parent account type.
- Cannot add child under a postable account.
- Normal balance must match account type.
- Postable account cannot have children.
- Circular parent references are blocked.

Computed properties:

- `level`
- `current_balance`

`current_balance`:

- Only for postable accounts.
- Uses posted journal items.
- Debit-normal: `debit - credit`.
- Credit-normal: `credit - debit`.

Limitation:

- Summary account balances are not recursively calculated.

### `Journal`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `name`
- `code`
- `type`
- `default_account`
- `is_active`

Journal types:

```text
sale
purchase
cash
bank
general
```

Default account validation:

- Must belong to same company.
- Must be postable.
- Must match journal type where applicable:
  - sale -> income
  - purchase -> expense
  - cash -> asset
  - bank -> asset

### `JournalEntry`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `journal`
- `entry_number`
- `date`
- `reference`
- `status`
- `notes`

Statuses:

```text
draft
posted
cancelled
```

Behavior:

- Auto-generates entry number using journal code:
  - Sequence key: `journal_{company_id}_{journal.code}`
  - Prefix: `{journal.code}-`
  - Padding: `4`
- Journal must belong to same company.
- Posted/cancelled entries cannot be normally edited.
- Posting requires non-empty balanced lines.
- Posted entries cannot be directly cancelled; reversal entries are expected but not implemented.

Properties:

- `total_debit`
- `total_credit`
- `is_balanced`

Methods:

- `post()`
- `cancel()`

### `JournalItem`

Extends `BaseModel`.

Fields:

- `entry`
- `account`
- `partner`
- `description`
- `debit`
- `credit`

Validation:

- Cannot edit lines of posted/cancelled entries.
- Debit/credit cannot be negative.
- One line cannot have both debit and credit.
- One line cannot have both zero.
- Account must be postable.
- Account must belong to same company as entry.
- Partner must belong to same company as entry.
- Partner requires account with `allow_reconciliation=True`.
- Account with `allow_reconciliation=True` requires a partner.

### `Payment`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `branch`
- `voucher_number`
- `partner`
- `payment_type`
- `payment_method`
- `account`
- `amount`
- `date`
- `status`
- `reference`
- `notes`
- `journal_entry`

Payment types:

```text
inbound
outbound
```

Payment methods:

```text
cash
bank
```

Code generation:

```text
inbound  -> REC- / receipt_branch_{branch_id}
outbound -> PAY- / payment_branch_{branch_id}
```

Validation:

- Branch, partner, and account must belong to same company.
- Amount must be greater than zero.
- Payment account must be postable.
- Payment account must be asset type.
- Inbound payment must use customer/both partner.
- Outbound payment must use supplier/both partner.

### `AccountingService`

Defined in `backend/apps/accounting/services/accounting_service.py`.

Helper methods:

```python
_get_or_create_journal(company, code, name, journal_type)
_get_account_by_code(company, code)
```

Main methods:

```python
create_purchase_invoice_entry(...)
create_sales_invoice_entry(...)
create_payment_journal_entry(...)
```

#### Purchase Invoice Accounting Entry

Method:

```python
create_purchase_invoice_entry(
    invoice,
    inventory_account_code="1004",
    payable_account_code="2001",
    expense_payment_account_code="1002",
)
```

Behavior:

- Creates/uses journal `PUR`, type `purchase`.
- Prevents duplicate entry by company/reference/journal.
- Calculates:
  - Goods value from item line totals.
  - Shipping cost.
  - Clearance cost.
  - Commission value from `commission_percentage`.
  - Total inventory value = goods + shipping + clearance + commission.
- Debits inventory account.
- Credits payable account for goods value.
- Credits expense/payment account for extra costs if any.
- Posts entry.

Limitation:

- Invoice model does not have a `journal_entry` field.
- Entry is not linked back to the invoice.
- Purchase posting service does not call this method.

#### Sales Invoice Accounting Entry

Method:

```python
create_sales_invoice_entry(
    invoice,
    receivable_account_code="1003",
    revenue_account_code="4001",
)
```

Behavior:

- Creates/uses journal `SAL`, type `sale`.
- Prevents duplicate entry by company/reference/journal.
- Debits receivable account.
- Credits revenue account.
- Posts entry.

Limitation:

- Invoice model does not have a `journal_entry` field.
- Entry is not linked back to the invoice.
- Sales posting service does not call this method.
- No COGS entry is created.

#### Payment Accounting Entry

Method:

```python
create_payment_journal_entry(
    payment,
    receivable_account_code="1003",
    payable_account_code="2001",
)
```

Behavior:

- Uses cash journal `CSH` or bank journal `BNK`.
- Uses payment account as cash/bank account.
- For outbound payments, checks sufficient cash/bank account balance.
- Outbound payment:
  - Debit payable.
  - Credit cash/bank.
- Inbound payment:
  - Debit cash/bank.
  - Credit receivable.
- Posts entry.

### `PaymentService`

Defined in `backend/apps/accounting/services/payment_service.py`.

Method:

```python
PaymentService.post_payment(payment)
```

Behavior:

- Requires draft status.
- Rejects payment if already linked to journal entry.
- Calls `AccountingService.create_payment_journal_entry`.
- Links journal entry to payment.
- Sets payment status to `posted`.

Payment posting is wired into Django admin via `backend/apps/accounting/admin/payment_admin.py`.

---

## `apps.ai_assistant`

Responsibilities:

- Upload PDF/DOCX documents.
- Extract text.
- Chunk text.
- Generate embeddings.
- Build and search FAISS indexes.
- Ask questions using Ollama/LangChain.
- Return citations.

Important files:

```text
backend/apps/ai_assistant/models/document.py
backend/apps/ai_assistant/services/extraction_service.py
backend/apps/ai_assistant/services/chunking_service.py
backend/apps/ai_assistant/services/embedding_service.py
backend/apps/ai_assistant/services/faiss_store_service.py
backend/apps/ai_assistant/services/document_processing_service.py
backend/apps/ai_assistant/services/qa_service.py
backend/apps/ai_assistant/api/serializers.py
backend/apps/ai_assistant/api/views.py
backend/apps/ai_assistant/api/urls.py
backend/apps/ai_assistant/README.md
backend/apps/ai_assistant/test_assets/
```

### `Document`

Extends `SoftDeleteModel`.

Fields:

- `company`
- `uploaded_by`
- `file`
- `original_filename`
- `file_type`
- `file_size`
- `status`
- `notes`

Statuses:

```text
uploaded
processing
ready
failed
```

Allowed extensions:

```python
{".pdf", ".docx"}
```

Upload path:

```text
ai_assistant/company_{company_id}/documents/{uuid}.{ext}
```

### `DocumentChunk`

Regular Django model, not `BaseModel`.

Fields:

- `id`
- `document`
- `company`
- `chunk_index`
- `text`
- `page_number`
- `char_start`
- `char_end`
- `embedding`
- `embedding_model`
- `created_at`

Constraint:

- Unique `document + chunk_index`.

### AI Services

#### `ExtractionService`

File:

```text
backend/apps/ai_assistant/services/extraction_service.py
```

Behavior:

- PDF extraction with `pypdf.PdfReader`.
- DOCX extraction with `python-docx`.
- Rejects unsupported file types.
- Raises a clear error for image-only/scanned PDFs with no extractable text.

#### `ChunkingService`

File:

```text
backend/apps/ai_assistant/services/chunking_service.py
```

Defaults:

- Chunk size: `1200`
- Overlap: `150`

Tracks:

- Text
- Page number
- Character start/end

#### `EmbeddingService`

File:

```text
backend/apps/ai_assistant/services/embedding_service.py
```

Default model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Behavior:

- Lazily loads and caches SentenceTransformer model.
- Produces normalized embeddings.

#### `FaissStoreService`

File:

```text
backend/apps/ai_assistant/services/faiss_store_service.py
```

Responsibilities:

- Build FAISS index.
- Save index and metadata.
- Search document chunks.
- Delete document index folder.

Index directory:

```text
MEDIA_ROOT/ai_assistant/faiss/company_{company_id}/{document_id}/
```

Files:

```text
index.faiss
metadata.json
```

FAISS index type:

```python
faiss.IndexFlatIP
```

#### `DocumentProcessingService`

File:

```text
backend/apps/ai_assistant/services/document_processing_service.py
```

Pipeline:

```text
set status processing
extract document text
chunk text
delete old chunks
bulk create chunks
build FAISS index
set status ready
```

On failure:

```text
set status failed
store exception message in notes
raise exception
```

#### `QAService`

File:

```text
backend/apps/ai_assistant/services/qa_service.py
```

Default model:

```text
llama3
```

Fallback answer:

```text
I could not find this information in the uploaded document.
```

Behavior:

- Performs semantic search.
- Builds citations.
- Builds a prompt instructing the model to answer only from context.
- Calls Ollama through LangChain integration.
- Returns answer and citations.

### AI API

Routes:

```text
GET    /api/ai-assistant/documents/
POST   /api/ai-assistant/documents/
GET    /api/ai-assistant/documents/{id}/
DELETE /api/ai-assistant/documents/{id}/
POST   /api/ai-assistant/documents/{id}/process/
GET    /api/ai-assistant/documents/{id}/chunks/
POST   /api/ai-assistant/documents/{id}/search/
POST   /api/ai-assistant/documents/{id}/ask/
```

Company scoping:

- Documents are filtered by `request.user.company`.

Destroy behavior:

- Deletes local FAISS index.
- Deletes physical uploaded file.
- Soft-deletes the document record.

---

## Database Design

### Core Entity Relationship Diagram

```text
Company
├── Branch
│   ├── User
│   ├── Warehouse
│   ├── SalesInvoice
│   ├── PurchaseInvoice
│   └── Payment
├── Partner
│   ├── SalesInvoice.customer
│   ├── PurchaseInvoice.supplier
│   ├── Payment.partner
│   └── JournalItem.partner
├── Product
│   ├── SalesInvoiceItem
│   ├── PurchaseInvoiceItem
│   ├── StockMovement
│   └── StockBalance
├── Category
├── Warehouse
│   ├── StockTransaction.source_warehouse
│   ├── StockTransaction.destination_warehouse
│   ├── StockBalance
│   ├── SalesInvoice
│   └── PurchaseInvoice
├── Account
│   ├── Journal.default_account
│   ├── JournalItem.account
│   └── Payment.account
├── Journal
│   └── JournalEntry
├── JournalEntry
│   └── JournalItem
└── Document
    └── DocumentChunk
```

### Document Flow Relationship

```text
SalesInvoice
└── SalesInvoiceItem
    └── Product

Posting SalesInvoice
└── StockTransaction(type=OUT)
    └── StockMovement
        └── Product
```

```text
PurchaseInvoice
└── PurchaseInvoiceItem
    └── Product

Posting PurchaseInvoice
└── StockTransaction(type=IN)
    └── StockMovement
        └── Product
```

```text
Payment
└── JournalEntry
    └── JournalItem
        ├── Account
        └── Partner
```

### Multi-Company Design

Most operational models include `company`. Key examples:

- `User`
- `Branch`
- `Partner`
- `Category`
- `Product`
- `Warehouse`
- `StockTransaction`
- `StockBalance`
- `SalesInvoice`
- `PurchaseInvoice`
- `Account`
- `Journal`
- `JournalEntry`
- `Payment`
- `Document`
- `DocumentChunk`

Validation usually enforces that related records belong to the same company.

API querysets commonly filter by:

```python
company=request.user.company
```

### Key Constraints

Important uniqueness and integrity constraints:

- Branch code unique per company among non-deleted branches.
- Partner code unique per company among non-deleted partners.
- Product SKU unique per company among non-deleted products.
- Warehouse code unique per company among non-deleted warehouses.
- Warehouse name unique per branch among non-deleted warehouses.
- Stock balance unique per company/product/warehouse.
- Sales invoice number unique per branch among non-deleted invoices.
- Purchase invoice number unique per branch among non-deleted invoices.
- Account code unique per company among non-deleted accounts.
- Journal code unique per company among non-deleted journals.
- Journal entry number unique per company among non-deleted entries.
- Payment voucher number unique per branch among non-deleted payments.
- AI document chunk index unique per document.

---

## Core Business Workflows

## Sales Workflow

### Sales API Flow

```text
1. POST /api/sales/invoices/
2. POST /api/sales/invoice-items/
3. POST /api/sales/invoices/{id}/post/
4. SalesService.post_invoice()
5. StockService.post_transaction()
6. Invoice status becomes posted
7. Stock balances are reduced
```

### Sales Posting Flow Diagram

```text
SalesInvoice(draft)
    │
    ├── validate has items
    ├── validate total_amount > 0
    ├── split stock items from service items
    │
    ├── if stock items exist:
    │       ├── require invoice.warehouse
    │       ├── create StockTransaction(type=OUT)
    │       ├── create StockMovement per non-service item
    │       └── StockService.post_transaction()
    │              ├── lock StockBalance rows
    │              ├── validate enough available quantity
    │              └── decrement quantity
    │
    └── set SalesInvoice.status = posted
```

Actual implementation:

- `backend/apps/sales/services/sales_service.py`
- `backend/apps/inventory/services/stock_service.py`

Missing in sales flow:

- No accounting journal entry.
- No invoice-to-journal relation.
- No COGS accounting.
- No reversal/cancellation flow.

## Purchase Workflow

### Purchase API Flow

```text
1. POST /api/purchases/invoices/
2. POST /api/purchases/invoice-items/
3. POST /api/purchases/invoices/{id}/post/
4. PurchaseService.post_invoice()
5. StockService.post_transaction()
6. Invoice status becomes posted
7. Stock balances are increased
8. Product average cost may update
```

### Purchase Posting Flow Diagram

```text
PurchaseInvoice(draft)
    │
    ├── validate has items
    ├── create StockTransaction(type=IN)
    │       └── source_warehouse = invoice.warehouse
    │
    ├── create StockMovement per invoice item
    │       └── unit_cost = item.unit_price
    │
    ├── StockService.post_transaction()
    │       ├── lock StockBalance rows
    │       ├── increment quantity
    │       └── update weighted average cost
    │
    └── set PurchaseInvoice.status = posted
```

Actual implementation:

- `backend/apps/purchases/services/purchase_service.py`
- `backend/apps/inventory/services/stock_service.py`

Missing in purchase flow:

- No accounting journal entry.
- No invoice-to-journal relation.
- Commission percentage not included in invoice total.
- No landed-cost allocation per item.
- No reversal/cancellation flow.

## Inventory Transaction Workflow

Manual stock transactions:

```text
1. POST /api/inventory/stock-transactions/
2. POST /api/inventory/stock-movements/
3. POST /api/inventory/stock-transactions/{id}/post/
```

Supported transaction types:

- `IN`
- `OUT`
- `TRANSFER`

### Inventory Posting Diagram

```text
StockTransaction(draft)
    │
    ├── load items
    ├── reject if no items
    │
    ├── IN:
    │     ├── lock/get StockBalance
    │     ├── quantity += item.quantity
    │     └── update product.average_cost
    │
    ├── OUT:
    │     ├── lock/get StockBalance
    │     ├── available = quantity - reserved_quantity
    │     ├── reject if available < item.quantity
    │     └── quantity -= item.quantity
    │
    └── TRANSFER:
          ├── lock source StockBalance
          ├── lock destination StockBalance
          ├── reject if source available is insufficient
          ├── source.quantity -= item.quantity
          └── destination.quantity += item.quantity
```

## Transfer Workflow

Internal transfer uses `StockTransaction(transaction_type="TRANSFER")`.

Required fields:

- `source_warehouse`
- `destination_warehouse`
- one or more `StockMovement` lines

Validation:

- Destination warehouse is required.
- Source and destination cannot be the same.
- Both warehouses must belong to same company.
- Source must have sufficient available quantity.

Missing:

- No in-transit status.
- No two-step dispatch/receive.
- No transfer approval.
- No reversal flow.

## Accounting Workflow

### Manual Journal Entry

```text
1. Create JournalEntry(draft)
2. Add JournalItems
3. Call entry.post()
4. Entry validates balanced debit/credit
5. Entry status becomes posted
6. Account and partner balances reflect posted items through aggregation
```

### Payment Posting

```text
Payment(draft)
    │
    ├── PaymentService.post_payment()
    ├── AccountingService.create_payment_journal_entry()
    │       ├── create cash or bank Journal
    │       ├── create JournalEntry
    │       ├── create two JournalItems
    │       └── post JournalEntry
    │
    ├── link Payment.journal_entry
    └── set Payment.status = posted
```

Inbound payment:

```text
Debit  cash/bank
Credit receivable
```

Outbound payment:

```text
Debit  payable
Credit cash/bank
```

### Invoice Accounting Services

Accounting service can create entries for sales and purchase invoices, but this is not wired to posting.

Sales accounting entry:

```text
Debit  receivable account 1003
Credit revenue account    4001
```

Purchase accounting entry:

```text
Debit  inventory account 1004
Credit payable account   2001
Credit cash account      1002 for extra costs
```

Important gap:

- `SalesInvoice` and `PurchaseInvoice` do not have `journal_entry` fields.
- Posting services do not call `AccountingService`.

## AI Assistant Workflow

```text
1. Upload PDF/DOCX
2. Document status = uploaded
3. POST process
4. Document status = processing
5. Extract text
6. Chunk text
7. Generate embeddings
8. Save chunks and embeddings
9. Build FAISS index
10. Document status = ready
11. Search or ask questions
12. Return citations
```

---

## API and Views

## Main API Mounts

Defined in `backend/config/urls.py`.

```text
/api/auth/
/api/partners/
/api/inventory/
/api/sales/
/api/purchases/
/api/ai-assistant/
/api/schema/
/api/docs/
/api/redoc/
```

## Auth API

```text
POST /api/auth/login/
POST /api/auth/refresh/
GET  /api/auth/me/
GET  /api/auth/context/
```

## Partners API

```text
GET    /api/partners/partners/
POST   /api/partners/partners/
GET    /api/partners/partners/{id}/
PATCH  /api/partners/partners/{id}/
DELETE /api/partners/partners/{id}/
GET    /api/partners/partners/customers/
GET    /api/partners/partners/suppliers/
```

## Inventory API

```text
GET    /api/inventory/units/
POST   /api/inventory/units/
GET    /api/inventory/units/{id}/
PATCH  /api/inventory/units/{id}/
DELETE /api/inventory/units/{id}/

GET    /api/inventory/products/
POST   /api/inventory/products/
GET    /api/inventory/products/{id}/
PATCH  /api/inventory/products/{id}/
DELETE /api/inventory/products/{id}/

GET    /api/inventory/warehouses/
POST   /api/inventory/warehouses/
GET    /api/inventory/warehouses/{id}/
PATCH  /api/inventory/warehouses/{id}/
DELETE /api/inventory/warehouses/{id}/

GET    /api/inventory/stock-transactions/
POST   /api/inventory/stock-transactions/
GET    /api/inventory/stock-transactions/{id}/
PATCH  /api/inventory/stock-transactions/{id}/
DELETE /api/inventory/stock-transactions/{id}/
POST   /api/inventory/stock-transactions/{id}/post/

GET    /api/inventory/stock-movements/
POST   /api/inventory/stock-movements/
GET    /api/inventory/stock-movements/{id}/
PATCH  /api/inventory/stock-movements/{id}/
DELETE /api/inventory/stock-movements/{id}/

GET    /api/inventory/stock-balances/
GET    /api/inventory/stock-balances/{id}/
```

## Sales API

```text
GET    /api/sales/invoices/
POST   /api/sales/invoices/
GET    /api/sales/invoices/{id}/
PATCH  /api/sales/invoices/{id}/
DELETE /api/sales/invoices/{id}/
POST   /api/sales/invoices/{id}/post/

GET    /api/sales/invoice-items/
POST   /api/sales/invoice-items/
GET    /api/sales/invoice-items/{id}/
PATCH  /api/sales/invoice-items/{id}/
DELETE /api/sales/invoice-items/{id}/
```

## Purchases API

```text
GET    /api/purchases/invoices/
POST   /api/purchases/invoices/
GET    /api/purchases/invoices/{id}/
PATCH  /api/purchases/invoices/{id}/
DELETE /api/purchases/invoices/{id}/
POST   /api/purchases/invoices/{id}/post/

GET    /api/purchases/invoice-items/
POST   /api/purchases/invoice-items/
GET    /api/purchases/invoice-items/{id}/
PATCH  /api/purchases/invoice-items/{id}/
DELETE /api/purchases/invoice-items/{id}/
```

## AI Assistant API

```text
GET    /api/ai-assistant/documents/
POST   /api/ai-assistant/documents/
GET    /api/ai-assistant/documents/{id}/
DELETE /api/ai-assistant/documents/{id}/
POST   /api/ai-assistant/documents/{id}/process/
GET    /api/ai-assistant/documents/{id}/chunks/
POST   /api/ai-assistant/documents/{id}/search/
POST   /api/ai-assistant/documents/{id}/ask/
```

## Accounting API

Accounting API is currently missing/not active.

There is an `apps.accounting.api` folder, but:

- `backend/config/urls.py` does not include it.
- The current accounting API files appear empty.

---

## Authentication and Permissions

Authentication is JWT-based for APIs.

Default DRF permissions require authenticated users.

User context includes:

- User
- Company
- Branch

Company scoping is implemented in most API querysets.

Admin permissions use:

- Django `Group`
- Django model permissions
- Unfold sidebar permission lambdas

Role constants exist in `apps.users.roles`.

Important limitations:

- Role setup command likely has incorrect imports/permission codenames.
- Object-level permission helper exists but is not broadly enforced by DRF.
- Branch-level permissions are not deeply enforced in API viewsets.
- `LoginRequiredMiddleware` may interfere with API behavior.

---

## Accounting Implementation

Accounting is one of the most important partially implemented parts.

Implemented:

- Account tree model.
- Journal model.
- Journal entry model.
- Journal item model.
- Payment model.
- Journal posting validation.
- Partner balance calculation through posted journal items.
- Payment posting into journal entries.
- Service methods for creating sales/purchase invoice accounting entries.

Not fully implemented:

- Accounting REST APIs.
- Frontend accounting UI.
- Sales/purchase posting integration with accounting.
- Invoice-to-journal relation.
- COGS accounting.
- Reversal/cancellation entries.
- Fiscal year enforcement.

Accounting should be treated as a strong domain foundation that needs integration work.

---

## Inventory and Warehouse Implementation

Inventory is more complete than accounting.

Implemented:

- Products.
- Units.
- Categories.
- Warehouses.
- Stock transactions.
- Stock movements.
- Stock balances.
- Posting logic for IN/OUT/TRANSFER.
- Average cost update on inbound stock.
- Stock checks on outbound and transfer.
- Sales posting creates OUT stock transactions.
- Purchase posting creates IN stock transactions.

Not fully implemented:

- Reservation workflow.
- Transfer approval/receipt.
- Stock valuation reports.
- Stock adjustment/reversal workflow.
- Inventory accounting integration.
- Stock transaction journal entry creation.

---

## AI Document Assistant

The AI assistant is isolated and does not mutate ERP business records.

Implemented:

- Upload PDF/DOCX.
- Validate extension.
- Extract text.
- Chunk text.
- Generate embeddings.
- Store embeddings in DB.
- Build FAISS index.
- Search chunks semantically.
- Ask questions using Ollama `llama3`.
- Return answer with citations.
- Delete document and local FAISS index.
- React UI demo page.

Limitations:

- Scanned PDFs are unsupported.
- Ollama must be running locally.
- `llama3` must be pulled.
- First embedding run may download model.
- Processing is synchronous, not background job based.
- Not a production document management system.

---

## Reports and Dashboard

Backend:

- No dedicated reporting app.
- No dedicated dashboard API.
- `StockBalanceViewSet` acts as a basic inventory inquiry endpoint.
- `backend/API_ROADMAP.md` explicitly defers additional reporting endpoints and dashboard APIs.

Frontend:

- `DashboardPage.tsx` fetches full lists and counts array lengths client-side.
- Cards shown:
  - Partners
  - Products
  - Warehouses
  - Stock Transactions
  - Stock Balances
  - Sales
  - Purchases

Current limitation:

- This approach does not scale for large datasets.
- Counts should eventually come from aggregation endpoints.

---

## Important Technical Decisions

### Modular Django Monolith

The project is split by business domain into Django apps. This keeps the system simple while still separating concerns.

### Service Layer for Business Logic

Posting logic lives in service classes:

- `StockService`
- `SalesService`
- `PurchaseService`
- `AccountingService`
- `PaymentService`
- AI assistant processing/search/QA services

This is important. Continue putting multi-step business workflows in services.

### UUID Primary Keys

Most custom models use UUID IDs through `BaseModel` or direct UUID fields. This is useful for APIs and avoids exposing sequential database IDs.

### Soft Delete

Most master/document models use `SoftDeleteModel`, enabling historical preservation and conditional uniqueness.

### Atomic Number Sequences

`Sequence.next_number()` uses row locks, making document number generation safer under concurrency.

### Draft/Post Document Lifecycle

Documents are generally editable only while draft. Posting creates business side effects.

### Company-Scoped Data

The system is designed for multi-company use. Most APIs and model validations enforce company consistency.

### Django Admin as Operational Surface

The Unfold admin configuration in `settings.py` defines a custom sidebar with Arabic labels and permission checks. Admin remains a major management interface.

---

## Important Files and Responsibilities

### Backend Configuration

```text
backend/config/settings.py
```

Defines apps, middleware, database, REST framework, JWT, CORS, drf-spectacular, Unfold admin.

```text
backend/config/urls.py
```

Main URL routing.

### Core

```text
backend/apps/core/models/base.py
```

BaseModel, SoftDeleteModel, audit logging.

```text
backend/apps/core/models/sequences.py
```

Atomic sequence generator.

```text
backend/apps/core/middleware.py
```

Thread-local user access for audit fields.

### Inventory

```text
backend/apps/inventory/services/stock_service.py
```

Inventory posting and average cost logic.

### Sales

```text
backend/apps/sales/services/sales_service.py
```

Sales invoice posting into stock.

### Purchases

```text
backend/apps/purchases/services/purchase_service.py
```

Purchase invoice posting into stock.

### Accounting

```text
backend/apps/accounting/services/accounting_service.py
```

Creates accounting entries for sales invoices, purchase invoices, and payments.

```text
backend/apps/accounting/services/payment_service.py
```

Posts payments and links journal entries.

### AI Assistant

```text
backend/apps/ai_assistant/services/document_processing_service.py
backend/apps/ai_assistant/services/faiss_store_service.py
backend/apps/ai_assistant/services/qa_service.py
```

Main RAG pipeline.

### Frontend

```text
frontend/src/App.tsx
```

Routes.

```text
frontend/src/lib/api/axios.ts
```

Axios client and bearer token injection.

```text
frontend/src/app/store/auth-store.ts
```

Persisted JWT auth state.

```text
frontend/src/features/*/
```

Feature-level API helpers, pages, and types.

---

## Tests

Important test files:

```text
backend/apps/inventory/tests/test_stock_service.py
backend/apps/purchases/tests/test_purchase_service.py
backend/apps/sales/tests/test_sales_service.py
backend/apps/accounting/tests/test_accounting_service.py
backend/apps/accounting/tests/test_entry_models.py
backend/apps/accounting/tests/test_payment_service.py
backend/apps/ai_assistant/tests.py
```

Test coverage includes:

- Stock IN increases stock and updates average cost.
- Stock OUT decreases stock.
- Stock OUT fails on insufficient stock.
- Transfers move stock between warehouses.
- Empty/non-draft stock transactions cannot be posted.
- Purchase invoice posting creates IN stock transaction and updates stock.
- Sales invoice posting reduces stock.
- Service products do not create stock movement.
- Journal entries must be balanced.
- Journal item cannot have both sides zero.
- Sales and purchase accounting entries balance correctly.
- Payment posting creates journal entries.
- AI document upload validation and extraction fixture checks.

Known test concern:

- Sales service tests expect a return value that does not match current service implementation.

Run backend tests:

```powershell
cd backend
python manage.py test
```

---

## Current Implementation Status

### Complete or Mostly Complete

- Django project setup.
- PostgreSQL settings.
- JWT auth API.
- Custom user model.
- Company and branch models.
- Partner model and API.
- Inventory master data models and APIs.
- Warehouse model and API.
- Stock transactions/movements/balances.
- Inventory posting service.
- Purchase invoice models/API/posting to inventory.
- Sales invoice models/API/posting to inventory.
- Accounting models.
- Accounting services.
- Payment posting service.
- AI document assistant backend and frontend demo.
- Swagger/ReDoc API docs.
- React protected route shell.
- React pages for main operational modules.

### Partial

- Accounting integration with sales and purchases.
- Permissions and roles.
- Reporting and dashboards.
- Cancellation/reversal behavior.
- Frontend CRUD completeness.
- Frontend auth lifecycle.
- AI production readiness.

### Missing

- Accounting REST APIs.
- Accounting frontend.
- Server-side dashboard APIs.
- Advanced reporting endpoints.
- Sales/purchase journal-entry linkage.
- COGS accounting.
- Inventory valuation reports.
- Stock reservations.
- Full transfer lifecycle.
- Approval workflows.
- Proper token refresh in frontend.

---

## Known Problems and Limitations

1. Accounting APIs are not mounted.

2. `apps.accounting.api` files appear empty or unused.

3. Sales and purchase posting do not create accounting entries.

4. Invoice models do not have `journal_entry` fields, despite accounting service checking `journal_entry_id`.

5. Sales service tests appear out of sync with the service return value.

6. Purchase commission percentage is used in accounting service but not included in invoice total recalculation.

7. Role setup command likely has import and permission-codename problems.

8. `LoginRequiredMiddleware` can interfere with API behavior.

9. Frontend API URL is hardcoded to `http://127.0.0.1:9000/api`.

10. Frontend has no token refresh interceptor.

11. `StockTransaction.source_warehouse` is semantically confusing for IN transactions.

12. Cancellation/reversal workflows are not implemented.

13. Dashboard counts fetch full lists client-side.

14. AI assistant requires local Ollama and may need model downloads.

15. Some source files contain Arabic labels/comments; terminal output can show mojibake if encoding is wrong.

---

## Scalability Concerns

### Backend

- Client-side dashboard counting will not scale.
- Account balance calculation aggregates journal items on demand.
- Partner balance calculation aggregates journal items on demand.
- Summary account balances are not precomputed.
- AI document processing is synchronous.
- FAISS index is local filesystem based, not distributed.
- No pagination settings are visible in DRF configuration.
- Some API list endpoints may return full datasets.
- No background job queue exists for heavy tasks.

### Frontend

- Hardcoded API base URL limits deployment flexibility.
- No token refresh creates poor UX for longer sessions.
- Inline styles and repeated table patterns may become hard to maintain.
- No accounting UI yet.

### Data Model

- Multi-company validation is mostly application-level, not enforced by tenant middleware.
- Fiscal year model exists but is not enforced during accounting posting.
- Cancellation/reversal is missing, which is critical for audit-safe ERP operations.

---

## Future Roadmap

Inferred from the code and `backend/API_ROADMAP.md`.

### Backend Roadmap

- Add accounting REST APIs.
- Add accounting frontend screens.
- Wire sales posting to accounting entry creation.
- Wire purchase posting to accounting entry creation.
- Add `journal_entry` links to sales and purchase invoice models.
- Add COGS accounting for sales.
- Add cancellation/reversal services for:
  - sales invoices
  - purchase invoices
  - stock transactions
  - journal entries
  - payments
- Add server-side dashboard aggregation endpoint.
- Add reporting endpoints:
  - stock valuation
  - low stock
  - partner balances
  - sales summary
  - purchase summary
  - account trial balance
- Add fiscal year enforcement.
- Fix role setup and permission codenames.
- Add object-level and branch-level API permissions.
- Add pagination and filtering consistently.
- Add background processing for AI assistant.

### Frontend Roadmap

- Add environment-based API URL.
- Add automatic refresh-token flow.
- Add accounting module UI.
- Add richer CRUD forms for partners/products/warehouses.
- Add stock transaction create/detail/post UI.
- Add reporting/dashboard pages using backend aggregates.
- Improve reusable UI components and reduce duplicated inline styling.
- Improve error handling and form validation.

### AI Roadmap

- Add background processing.
- Add OCR for scanned PDFs.
- Add progress status.
- Add per-company storage quotas.
- Add document collections.
- Add chat history.
- Add production-safe model/provider configuration.

---

## Developer Notes

### Run Backend

```powershell
cd backend
pip install -r requirements.txt
python manage.py check
python manage.py runserver 9000
```

### Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Run Tests

```powershell
cd backend
python manage.py test
```

### AI Assistant Requirements

For Ask endpoint:

```powershell
ollama pull llama3
ollama serve
```

### API Docs

```text
http://127.0.0.1:9000/api/docs/
http://127.0.0.1:9000/api/redoc/
```

### Coding Guidance for Future Work

When adding features:

- Keep model invariants in model `clean()` methods.
- Keep multi-step workflows in service classes.
- Use `transaction.atomic()` for posting or reversal logic.
- Use `select_for_update()` where stock/account balances must be protected.
- Preserve draft/post read-only semantics.
- Scope APIs by `request.user.company`.
- Prefer adding tests around posting side effects.
- Avoid bypassing service classes from views.

---

## Summary for Next Assistant

This project is a modular Django ERP with a React frontend. Its strongest implemented areas are inventory, sales/purchase invoice basics, payment accounting, and the AI document assistant. The most important architecture pattern is service-layer posting: documents are created as drafts, line items are added, and posting services create stock or accounting side effects inside transactions.

The system is multi-company and partially multi-branch. Most business models validate company consistency, and most APIs filter by the authenticated user's company. Document numbers are generated by the shared `Sequence` model using row locks.

The largest gap is accounting integration. Accounting models and services exist, but sales and purchase posting do not create or link journal entries. Accounting APIs and frontend screens are also missing. Cancellation and reversal flows are not implemented, despite status fields existing.

When continuing development, protect the existing domain rules:

- Draft documents are editable; posted documents are not.
- Stock updates must go through `StockService`.
- Sales and purchase posting should remain transactional.
- Accounting entries must be balanced before posting.
- Company/branch consistency matters everywhere.
- Do not invent missing workflows without adding explicit models/services/tests.

The best next architectural improvements are:

1. Fix and expose accounting APIs.
2. Add invoice-to-journal-entry relationships.
3. Integrate accounting into sales and purchase posting.
4. Implement reversal/cancellation services.
5. Replace frontend client-side dashboard counting with backend aggregate APIs.
6. Fix role setup and permission enforcement.
7. Add token refresh and environment-based API configuration to the frontend.

