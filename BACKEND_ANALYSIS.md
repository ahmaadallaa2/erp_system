# Django ERP Backend - Comprehensive Technical Analysis

**Date**: May 18, 2026  
**Scope**: backend/apps/* (models, services, API views/serializers)  
**Version**: MVP with multi-company architecture

---

## 1. DATA MODELS OVERVIEW

### 1.1 Core Models (apps/core/)

#### **Company** (SoftDeleteModel)
- UUID primary key
- Multi-tenant root entity
- Fields: name, logo, tax_number, commercial_record, email, phone, website, address
- One-to-many: Branch, Product, Warehouse, Partner, Account, Journal, User, etc.
- **Role**: Tenant isolation boundary for entire system

#### **Branch** (SoftDeleteModel)
- FK: Company (required, CASCADE)
- Code auto-generated: "BR-001" format (Sequence-based)
- Unique constraint: (company, code) when not deleted
- Fields: name, code, address, phone, is_active
- One-to-many: Warehouse, SalesInvoice, PurchaseInvoice, Payment
- **Role**: Sub-organizational unit within company

#### **BaseModel** (Abstract)
- UUID primary key, auto-generated
- Audit tracking: created_at, updated_at, created_by_id, updated_by_id (FK to User)
- Auto-logging via `_log_audit()` - tracks CREATE/UPDATE with changes
- Gets current user from middleware: `get_current_user()`
- Inherits: SalesInvoiceItem, PurchaseInvoiceItem, StockMovement, JournalItem

#### **SoftDeleteModel** (extends BaseModel, Abstract)
- Fields: is_deleted (bool, db_indexed), deleted_at, deleted_by_id (FK to User)
- Custom manager: `objects` (filtered, soft-deleted excluded), `all_objects` (unfiltered)
- `delete()` method overridden to call `soft_delete()` instead of hard delete
- Inherits: Company, Branch, User, Product, Warehouse, Category, Unit, Account, Journal, JournalEntry, SalesInvoice, PurchaseInvoice, Partner, Payment

#### **Sequence** (models.Model)
- Atomic number generation for document numbering
- Fields: key (unique), prefix, current_value, padding
- Uses `select_for_update()` + transaction.atomic for concurrency safety
- Creates new Sequence on first use if doesn't exist (handles race conditions)
- **Method**: `next_number(key, prefix, padding)` → returns formatted string

#### **AuditLog** (models.Model, no soft-delete)
- GenericForeignKey to any model
- Fields: user_id, action (CREATE/UPDATE/DELETE/RESTORE), changes (JSONField), timestamp, ip_address, browser_info
- Indexes: (content_type, object_id, -timestamp), user, action
- Triggered by BaseModel.save() for all auto-tracked models

### 1.2 Users Model (apps/users/)

#### **User** (AbstractUser override)
- Email-based authentication (username=None)
- UUID primary key
- Fields: full_name, phone, job_title
- user_type: system_admin, company_admin, branch_manager, employee
- Multi-tenant FK: company (nullable), branch (nullable)
- Validations:
  - branch.company_id == company_id (must match)
  - company_admin requires company
  - branch_manager requires both company and branch
- `soft_delete()` sets is_active=False instead of hard delete
- CustomUserManager for email-based login

### 1.3 Partners Model (apps/partners/)

#### **Partner** (SoftDeleteModel)
- FK: Company (CASCADE)
- partner_type: customer, supplier, both
- Code auto-generated: "CUST-001" / "SUP-001" / "PRT-001"
- Unique constraint: (company, code) when not deleted
- Fields: name, phone, mobile, email, website, address, city, tax_number, commercial_record
- Financial: credit_limit, initial_balance
- FK: responsible (User, SET_NULL, nullable)
- is_active, notes

---

## 2. INVENTORY MODELS (apps/inventory/)

### 2.1 Product Structure

#### **Product** (SoftDeleteModel)
- FK: Company (CASCADE), Category (SET_NULL), Unit (PROTECT)
- product_type: storable, service, consumable
- Code auto-generated via Sequence: "PROD-000001"
- Unique constraint: (company, sku) when not deleted
- Fields: name, sku, barcode, description, image, cost_price, average_cost, sale_price, reorder_point
- Accounting FKs: income_account (RESTRICT), expense_account (RESTRICT) - both nullable, allows category fallback
- Validations: category.company_id == company_id, account companies match
- **Critical**: average_cost updated by StockService on IN transactions (weighted average)

#### **Category** (SoftDeleteModel)
- FK: Company (CASCADE)
- Tree structure: parent FK (self, SET_NULL)
- Unique constraint: (company, name, parent) when not deleted
- Validation: parent.company_id == company_id

#### **Unit** (SoftDeleteModel)
- NOT company-scoped (global/shared across all companies)
- Unique constraints: name, short_name (both global)
- Fields: name, short_name, is_active

#### **Warehouse** (SoftDeleteModel)
- FK: Company (CASCADE), Branch (CASCADE), User/keeper (SET_NULL)
- warehouse_type: main, sub (showroom)
- Code auto-generated: "WH-0001"
- Unique constraints:
  - (branch, name) when not deleted
  - (company, code) when not deleted
- Validations: branch.company_id == company_id, keeper.company_id == company_id

### 2.2 Stock Management Models

#### **StockBalance** (BaseModel)
- FK: Company (CASCADE), Product (PROTECT), Warehouse (PROTECT)
- Unique constraint: (company, product, warehouse)
- Fields: quantity, reserved_quantity, location, reorder_point
- Property: `available_quantity` = quantity - reserved_quantity
- **Read-only**: Updated only via StockService, never directly by users
- Validations: Product and Warehouse must match company

#### **StockTransaction** (SoftDeleteModel)
- FK: Company (CASCADE), Warehouse/source (PROTECT), Warehouse/destination (PROTECT, nullable)
- transaction_type: IN (warin), OUT (sarif), TRANSFER (tahwil)
- Code auto-generated: "IN-00001", "OUT-00001", "TRF-00001"
- Unique constraint: (company, code)
- status: draft, posted, cancelled
- Fields: date, reference, notes
- FK: journal_entry (OneToOne, SET_NULL) - link to accounting entry
- Validations:
  - TRANSFER requires destination_warehouse and source ≠ destination
  - IN/OUT don't allow destination_warehouse
  - Warehouses must match company

#### **StockMovement** (BaseModel)
- FK: StockTransaction (CASCADE), Product (PROTECT)
- Fields: quantity, unit_cost, note
- Validations:
  - quantity > 0
  - unit_cost >= 0
  - Product.company_id == StockTransaction.company_id
  - Services cannot create movements
  - Cannot edit/delete if transaction.status == 'posted'
- **Immutability**: Locked after transaction posting

---

## 3. SALES MODELS (apps/sales/)

### 3.1 Sales Invoice Structure

#### **SalesInvoice** (SoftDeleteModel)
- FK: Company (RESTRICT), Branch (RESTRICT), Partner/customer (RESTRICT, limit_choices_to customer/both), Warehouse (RESTRICT, nullable)
- invoice_number auto-generated: "SINV-00001" per branch via Sequence(branch_id)
- Unique constraint: (branch, invoice_number) when not deleted
- status: draft, posted, cancelled
- Fields: date, total_amount (auto-calculated, editable=False), notes
- FK: journal_entry (OneToOne, PROTECT) - link to accounting
- Validations:
  - customer.partner_type in [customer, both]
  - All FKs must match company_id
  - Cannot modify items if posted

#### **SalesInvoiceItem** (BaseModel)
- FK: SalesInvoice (CASCADE), Product (RESTRICT)
- Fields: quantity, unit_price, line_total (auto-calculated), notes
- Validations:
  - quantity > 0
  - unit_price >= 0
  - Product.company_id == SalesInvoice.company_id
  - Cannot edit/delete if invoice.status == 'posted'
- Auto-calculation: line_total = quantity × unit_price (ROUND_HALF_UP)
- **Side effect**: save() calls `update_invoice_total()` (recalculates parent)
- delete() also triggers parent recalculation

---

## 4. PURCHASES MODELS (apps/purchases/)

### 4.1 Purchase Invoice Structure

#### **PurchaseInvoice** (SoftDeleteModel)
- FK: Company (RESTRICT), Branch (RESTRICT), Partner/supplier (RESTRICT, limit_choices_to supplier/both), Warehouse (RESTRICT)
- invoice_number auto-generated: "PINV-00001" per branch
- Unique constraint: (branch, invoice_number) when not deleted
- status: draft, posted, cancelled
- Fields: invoice_date, vendor_bill_number, total_amount (auto, editable=False), shipping_cost, clearance_cost, commission_percentage
- FK: journal_entry (OneToOne, PROTECT)
- Validations: All FKs match company_id

#### **PurchaseInvoiceItem** (BaseModel)
- FK: PurchaseInvoice (CASCADE), Product (RESTRICT)
- Fields: quantity, unit_price, line_total (auto), notes
- Validations: Same as SalesInvoiceItem
- **Calculation**: line_total = quantity × unit_price; invoice total += shipping_cost + clearance_cost
- delete() recalculates with cost additions

---

## 5. ACCOUNTING MODELS (apps/accounting/)

### 5.1 Chart of Accounts

#### **Account** (SoftDeleteModel)
- FK: Company (CASCADE)
- Code unique per company when not deleted
- Tree structure: parent FK (self, RESTRICT, nullable)
- account_type: asset, liability, equity, income, expense
- normal_balance: debit or credit (determined by type - NATURAL_BALANCE_MAP)
- Fields: name, is_postable, allow_reconciliation, is_active
- Indexes: (company, code), (company, parent), (company, account_type), (company, is_active)
- Validations:
  - parent != self (circular reference check)
  - parent.company_id == company_id
  - parent.account_type == account_type
  - parent must be non-postable (summary accounts can't post directly)
  - normal_balance must match account_type (NATURAL_BALANCE_MAP)
  - If is_postable=True, cannot have children
  - Recursive circular reference detection
- Property: `level` = depth in tree
- Property: `current_balance` = SUM(debit) - SUM(credit) for posted entries (adjusted for normal_balance)

#### **Journal** (SoftDeleteModel)
- FK: Company (CASCADE)
- Unique constraint: (company, code) when not deleted
- type: sale, purchase, cash, bank, general
- Fields: name, code, default_account (FK RESTRICT, nullable), is_active
- Indexes: (company, code), (company, type), (company, is_active)
- Validations:
  - default_account.company_id == company_id
  - default_account must be postable
  - default_account.account_type must match journal type (JOURNAL_ACCOUNT_TYPE_MAP)

#### **JournalEntry** (SoftDeleteModel)
- FK: Company (CASCADE), Journal (RESTRICT)
- entry_number auto-generated: "{journal.code}-0001"
- Unique constraint: (company, entry_number) when not deleted
- status: draft, posted, cancelled
- Fields: date, reference, notes
- Indexes: (company, date), (company, status), (company, reference)
- Properties:
  - `total_debit`: SUM(items.debit)
  - `total_credit`: SUM(items.credit)
  - `is_balanced`: total_debit == total_credit && total_debit > 0
- Validations:
  - journal.company_id == company_id
  - Cannot edit if already posted/cancelled (must create reversal)
  - At posting: entry must be balanced
- Methods:
  - `post()`: Changes draft → posted (validates balance)
  - `cancel()`: draft → cancelled (posted entries need reversal instead)
  - `validate_balanced()`: Ensures debit = credit and > 0

#### **JournalItem** (BaseModel)
- FK: JournalEntry (CASCADE), Account (RESTRICT), Partner (SET_NULL, nullable)
- Fields: description, debit, credit
- Validations:
  - Cannot edit if entry.status in [posted, cancelled]
  - debit >= 0, credit >= 0
  - debit > 0 XOR credit > 0 (exactly one must be non-zero)
  - account.is_postable == True
  - account.company_id == entry.company_id
  - If partner specified: partner.company_id == entry.company_id
  - If account.allow_reconciliation: partner must be set
  - If account.allow_reconciliation: partner is mandatory

### 5.2 Payments

#### **Payment** (SoftDeleteModel)
- FK: Company (RESTRICT), Branch (RESTRICT), Partner (RESTRICT), Account (RESTRICT)
- payment_type: inbound (qabz), outbound (sarf)
- payment_method: cash, bank
- status: draft, posted, cancelled
- Fields: voucher_number (auto), amount, date, reference (check number), notes
- FK: journal_entry (OneToOne, SET_NULL)
- Unique constraint: (branch, voucher_number) when not deleted
- Indexes: (company, date), (company, payment_type), (company, status)
- Validations:
  - All FKs match company_id
  - amount > 0
  - account.is_postable == True
  - account.account_type == 'asset' (cash/bank only)
  - inbound: partner.partner_type in [customer, both]
  - outbound: partner.partner_type in [supplier, both]

---

## 6. DATABASE RELATIONSHIPS & INTEGRITY

### 6.1 Foreign Key Cascade Rules

| Model | FK Destination | On Delete | Notes |
|-------|-----------------|-----------|-------|
| Branch | Company | CASCADE | All branches deleted if company deleted |
| User | Company | CASCADE | Users tied to company |
| User | Branch | SET_NULL | Branch can be changed |
| Product | Company | CASCADE | All products deleted if company deleted |
| Product | Category | SET_NULL | Category removal orphans product |
| Product | Unit | PROTECT | Cannot delete unit with products |
| Product | Account (income/expense) | RESTRICT | Cannot delete account with products assigned |
| Warehouse | Company | CASCADE | All warehouses deleted if company deleted |
| Warehouse | Branch | CASCADE | Warehouses deleted if branch deleted |
| StockBalance | Product | PROTECT | Cannot delete product with balances |
| StockBalance | Warehouse | PROTECT | Cannot delete warehouse with balances |
| StockMovement | StockTransaction | CASCADE | All movements deleted if transaction deleted |
| StockMovement | Product | PROTECT | Cannot delete product with movements |
| SalesInvoice | Warehouse | RESTRICT | Cannot delete warehouse if has invoices |
| SalesInvoice | Account (income/expense) | RESTRICT | Account protection |
| SalesInvoiceItem | Product | RESTRICT | Cannot delete product with line items |
| PurchaseInvoice | Warehouse | RESTRICT | Warehouse protection |
| PurchaseInvoiceItem | Product | RESTRICT | Product protection |
| Account | Account (parent) | RESTRICT | Cannot delete parent account with children |
| Journal | Account (default) | RESTRICT | Cannot delete account used as default |
| JournalEntry | Account | RESTRICT | Cannot delete account with entries |
| Payment | Account | RESTRICT | Cannot delete account with payments |

### 6.2 Unique Constraints with Soft Delete

All use `condition=Q(is_deleted=False)`:

```python
# Allows soft-deleted records to release their codes
UniqueConstraint(fields=['company', 'code'], condition=Q(is_deleted=False))
```

**Models affected**: Company (implicit), Branch, Product, Warehouse, Category, Account, Journal, JournalEntry, SalesInvoice, PurchaseInvoice, StockTransaction, Partner, Payment

**Effect**: Deleted records don't block reuse of codes

### 6.3 Multi-Company Data Isolation

Every model has company FK (directly or through parent):
- Company → cascades to all children
- Branch → ensures hierarchical isolation
- User.company → defines scoping boundary
- All API querysets filtered by `user.company`

**Potential Issue**: Unit model is NOT company-scoped (global)

---

## 7. KEY API ENDPOINTS & SERIALIZERS

### 7.1 Accounting API

#### **AccountLookupViewSet** (ReadOnly)
- GET `/api/accounts/lookup/` → List active, postable accounts
- Filters: account_type (asset/liability/equity/income/expense), search (code/name)
- Scoped: user.company
- Serializer: AccountLookupSerializer (minimal: id, code, name, type, normal_balance, is_postable, is_active)

#### **JournalEntryViewSet** (Retrieve only)
- GET `/api/accounting/entries/{id}/` → Detail with all journal_items
- Relations: journal (basic), items (with account/partner details)
- Computed: total_debit, total_credit
- Scoped: user.company

#### **PaymentViewSet** (CRUD)
- GET `/api/payments/` → List (filters: status, payment_type, payment_method, partner)
- POST `/api/payments/` → Create draft payment
- Validation: User company/branch auto-set on create
- Serializer enforces: partner.company_id == user.company_id, account.company_id == user.company_id
- READ_ONLY: voucher_number (auto), status, journal_entry

### 7.2 Inventory API

**Registered in router**:
- `/api/units/` → UnitViewSet
- `/api/products/` → ProductViewSet
- `/api/warehouses/` → WarehouseViewSet
- `/api/stock-transactions/` → StockTransactionViewSet
- `/api/stock-movements/` → StockMovementViewSet
- `/api/stock-balances/` → StockBalanceViewSet

**Reports**:
- GET `/api/reports/product-movements/`
- GET `/api/reports/warehouse-balances/`

### 7.3 Sales API

**Registered in router**:
- `/api/sales-invoices/`
- `/api/sales-invoice-items/`

### 7.4 Purchases API

**Registered in router**:
- `/api/purchase-invoices/`
- `/api/purchase-invoice-items/`

---

## 8. BUSINESS LOGIC SERVICES

### 8.1 StockService (inventory/services/stock_service.py)

#### **post_transaction(transaction_obj)** [ATOMIC]
- Input: draft StockTransaction
- **IN**: Adds to StockBalance.quantity, updates Product.average_cost (weighted)
- **OUT**: Validates available_quantity >= required, decreases StockBalance.quantity
- **TRANSFER**: Validates source stock, transfers quantity between warehouses
- Output: Marks transaction as 'posted'
- Raises: ValueError if insufficient stock, empty transaction, or wrong status
- **Atomicity**: Uses `select_for_update()` on StockBalance for concurrency safety

#### **create_movement(transaction_obj, product, quantity, unit_cost, note)**
- Creates StockMovement line item
- Validates: transaction.status == 'draft'
- Raises: ValueError if not draft

#### **_update_average_cost_on_in(product, incoming_qty, incoming_unit_cost)** [INTERNAL]
- Weighted average: new_avg_cost = (old_qty × old_cost + new_qty × new_cost) / total_qty
- Updates Product.average_cost only on IN transactions
- Rounding: ROUND_HALF_UP to 2 decimals

### 8.2 SalesService (sales/services/sales_service.py)

#### **post_invoice(invoice)** [ATOMIC]
- Input: draft SalesInvoice
- **Validation**: Not draft, not empty, total > 0
- **Stock**: Filters items to only storable products (skips services)
- **Step 1**: Creates StockTransaction(OUT) if storable items exist
- **Step 2**: For each storable item, creates StockMovement with product.average_cost
- **Step 3**: Calls StockService.post_transaction()
- **Step 4**: Creates journal entry via AccountingService.create_sales_invoice_entry()
- **Step 5**: Marks invoice as 'posted', links journal_entry
- Output: StockTransaction or None
- **Important**: Requires warehouse if has storable items

### 8.3 PurchaseService (purchases/services/purchase_service.py)

#### **post_invoice(invoice)** [ATOMIC]
- Input: draft PurchaseInvoice
- **Validation**: Not draft, not empty
- **Step 1**: Creates StockTransaction(IN) with all items
- **Step 2**: Creates StockMovements with unit_price from line items
- **Step 3**: Posts transaction (updates stock, average cost)
- **Step 4**: Creates journal entry (accounting)
- **Step 5**: Marks invoice as 'posted'
- Output: StockTransaction

### 8.4 AccountingService (accounting/services/accounting_service.py)

#### **create_purchase_invoice_entry(invoice)** [ATOMIC]
- **Debit**: Inventory account (1004, configurable)
- **Credit**: Payable account (2001, configurable)
- Creates JournalEntry with 2 JournalItems
- Validates: No duplicate entry already exists for this invoice
- Posts entry automatically
- Used by: PurchaseService

#### **create_sales_invoice_entry(invoice)** [ATOMIC]
- **Account codes** (configurable):
  - 1003: Receivable (Debit)
  - 4001: Revenue (Credit)
  - 5001: COGS (Debit)
  - 1004: Inventory (Credit)
- **Entry**: 2-4 lines:
  - Receivable DR / Revenue CR (main revenue)
  - COGS DR / Inventory CR (if products exist)
- Calculates COGS: SUM(item.quantity × product.average_cost) for non-services
- Posts entry automatically
- Used by: SalesService

#### **create_payment_journal_entry(payment)** [ATOMIC]
- **Inbound** (from customer):
  - DR: Cash/Bank account
  - CR: Receivable account (1003)
- **Outbound** (to supplier):
  - DR: Payable account (2001)
  - CR: Cash/Bank account
- Validates:
  - Outbound: Cash/bank balance >= payment.amount
  - Account types match (asset for cash/bank, etc.)
- Posts entry automatically
- Used by: PaymentService

### 8.5 PaymentService (accounting/services/payment_service.py)

#### **post_payment(payment)** [ATOMIC]
- Input: draft Payment
- **Step 1**: Calls AccountingService.create_payment_journal_entry()
- **Step 2**: Links journal_entry to payment
- **Step 3**: Marks payment as 'posted'
- Output: JournalEntry

---

## 9. CONSTRAINTS, DEFAULTS & VALIDATORS

### 9.1 Auto-Generated Codes

| Model | Sequence Key Pattern | Prefix | Padding | Scope |
|-------|----------------------|--------|---------|-------|
| Product | product_sku_comp_{company_id} | PROD- | 6 | Per company |
| Warehouse | warehouse_code_comp_{company_id} | WH- | 4 | Per company |
| Partner | (varies by type) | CUST-/SUP-/PRT- | 3-6 | Per company |
| Branch | branch_code_comp_{company_id} | BR- | 3 | Per company |
| SalesInvoice | sinv_branch_{branch_id} | SINV- | 5 | Per branch |
| PurchaseInvoice | pinv_branch_{branch_id} | PINV- | 5 | Per branch |
| StockTransaction | stock_in/out/transfer_comp_{company_id} | IN-/OUT-/TRF- | 5 | Per company |
| JournalEntry | journal_{company_id}_{journal_code} | {journal_code}- | 4 | Per journal per company |
| Payment | receipt/payment_branch_{branch_id} | REC-/PAY- | 5 | Per branch |

### 9.2 Decimal Precision

- All monetary fields: max_digits=12, decimal_places=2
- Rounding: ROUND_HALF_UP (0.005 → 0.01)
- Quantities: max_digits=10-12, decimal_places=2

### 9.3 Model-Level Validations (clean() methods)

#### Company
- None (minimal model)

#### Branch
- branch.code must be unique per company (soft-deleted excluded)

#### User
- branch.company_id == company_id (if both set)
- company_admin requires company
- branch_manager requires company AND branch
- is_active=False is soft-delete

#### Product
- category.company_id == company_id
- income_account.company_id == company_id (if set)
- expense_account.company_id == company_id (if set)
- sku auto-generated if blank
- product_type=service cannot have stock movements

#### Warehouse
- branch.company_id == company_id
- keeper.company_id == company_id (if set)
- code auto-generated if blank

#### StockBalance
- product.company_id == company_id
- warehouse.company_id == company_id
- quantity - reserved_quantity >= 0 (via property, not validated)

#### StockTransaction
- source_warehouse.company_id == company_id
- destination_warehouse.company_id == company_id (if set)
- TRANSFER requires destination_warehouse
- TRANSFER: source ≠ destination
- IN/OUT cannot have destination_warehouse

#### StockMovement
- quantity > 0
- unit_cost >= 0
- product.company_id == transaction.company_id
- product.product_type != 'service'
- Cannot edit/delete if transaction.status == 'posted'

#### SalesInvoice
- customer.partner_type in [customer, both]
- branch.company_id == company_id
- customer.company_id == company_id
- warehouse.company_id == company_id (if set)
- Cannot modify items if posted

#### SalesInvoiceItem
- quantity > 0
- unit_price >= 0
- product.company_id == invoice.company_id
- Cannot edit/delete if invoice.status == 'posted'

#### PurchaseInvoice
- supplier.partner_type in [supplier, both]
- branch.company_id == company_id
- supplier.company_id == company_id
- warehouse.company_id == company_id

#### PurchaseInvoiceItem
- Same as SalesInvoiceItem

#### Account
- parent != self (circular reference)
- parent.company_id == company_id
- parent.account_type == account_type
- If parent: parent.is_postable == False (parent must be summary)
- normal_balance matches NATURAL_BALANCE_MAP[account_type]
- If is_postable: cannot have children
- Recursive circular reference detection via _check_circular_reference()

#### Journal
- default_account.company_id == company_id (if set)
- default_account.is_postable == True (if set)
- default_account.account_type must match JOURNAL_ACCOUNT_TYPE_MAP[type]

#### JournalEntry
- journal.company_id == company_id
- Cannot edit if status in [posted, cancelled]
- At posting: total_debit == total_credit AND > 0
- Cannot be empty when posting

#### JournalItem
- Cannot edit if entry.status in [posted, cancelled]
- debit >= 0, credit >= 0
- debit > 0 XOR credit > 0 (exactly one)
- debit == 0 AND credit == 0 → error
- account.is_postable == True
- account.company_id == entry.company_id
- If partner: partner.company_id == entry.company_id
- If account.allow_reconciliation: partner is MANDATORY
- If partner set AND account doesn't allow_reconciliation: error

#### Partner
- code auto-generated if blank
- Unique: (company, code) when not deleted

#### Payment
- branch.company_id == company_id
- partner.company_id == company_id
- account.company_id == company_id
- amount > 0
- account.is_postable == True
- account.account_type == 'asset'
- inbound: partner.partner_type in [customer, both]
- outbound: partner.partner_type in [supplier, both]
- outbound: cash_balance >= amount (in AccountingService)

---

## 10. STATUS/STATE MANAGEMENT

### 10.1 Document Lifecycle

All transactional documents follow:

```
Draft → Posted → [Cancelled (if not posted) OR just Posted]
```

**Blocked transitions**:
- draft → anything except posted/cancelled
- posted/cancelled → modified directly (need reversal entries)

### 10.2 Status Fields by Model

| Model | Status Choices | Initial | Rules |
|-------|---|---|---|
| StockTransaction | draft, posted, cancelled | draft | Can post only from draft; cannot modify items after posted |
| SalesInvoice | draft, posted, cancelled | draft | Cannot modify items after posted |
| PurchaseInvoice | draft, posted, cancelled | draft | Cannot modify items after posted |
| JournalEntry | draft, posted, cancelled | draft | Must be balanced to post; cannot modify after posted |
| Payment | draft, posted, cancelled | draft | Cannot modify after posted |

### 10.3 Immutability After Posting

- StockMovement items: Locked if transaction.status != 'draft'
- SalesInvoiceItem: Locked if invoice.status != 'draft'
- PurchaseInvoiceItem: Locked if invoice.status != 'draft'
- JournalItem: Locked if entry.status in [posted, cancelled]

**Enforcement**: save() and delete() throw ValidationError if locked

---

## 11. MULTI-COMPANY & BRANCH SCOPING

### 11.1 Isolation Levels

#### **Company-Level Isolation**
- Master data (Product, Warehouse, Partner, Account, Journal)
- Transaction data (SalesInvoice, PurchaseInvoice, StockTransaction, Payment, JournalEntry)
- All soft-deleted records retained for audit
- FK Company(CASCADE) ensures data deleted with company

#### **Branch-Level Isolation**
- Document numbering: SalesInvoice, PurchaseInvoice, Payment per branch
- Warehouses: Assigned to branch
- Users: Can be assigned to branch (optional - system admins may not have branch)

#### **User Context Enforcement**
```python
# API QuerySet pattern
queryset.filter(company=user.company, branch=user.branch)

# For system admin (no branch):
if user.user_type == 'system_admin':
    queryset.filter(company=user.company)  # All branches
else:
    queryset.filter(company=user.company, branch=user.branch)  # Specific branch
```

### 11.2 Data Scoping Issues Identified

#### **CRITICAL**: Unit Model
- NOT company-scoped
- Global across all companies
- Shared via Product FK
- **Risk**: Company A unit conflicts with Company B unit
- **Recommendation**: Make Unit company-scoped or create UnitAssignment junction model

#### **MODERATE**: Category Model
- Company-scoped via Product → Category relationship
- But Category itself has company_id
- Tree structure only within company
- **Status**: ✓ Properly scoped

#### **PARTIAL**: Account Reconciliation
- Partner optional on JournalItem but mandatory if account.allow_reconciliation
- Could expose partner across company boundary if validation fails
- **Status**: ✓ Validated at clean() level

---

## 12. VALIDATION LOGIC FLOW

### 12.1 Save Flow Example (Product)

```
1. User submits POST /api/products/
2. Serializer validates JSON schema
3. Model.full_clean() called in save()
   a. Checks product_type vs. company assignment
   b. Validates account company assignments
   c. Validates category company assignment
   d. Runs model clean() method
4. If no sku: Sequence.next_number() generates it (atomic)
5. BaseModel.save() called:
   a. Sets created_by/updated_by from get_current_user()
   b. Saves to DB
   c. AuditLog created with action=CREATE
6. Response 201 Created
```

### 12.2 Stock Transaction Posting Flow

```
1. POST /api/stock-transactions/{id}/actions/post/
2. StockService.post_transaction(transaction_obj):
   a. Validates: status == 'draft', has items
   b. For each item (atomic transaction):
      - SELECT FOR UPDATE StockBalance
      - If IN: quantity += item.quantity; update average_cost
      - If OUT: validate available >= quantity; quantity -= item.quantity
      - If TRANSFER: move quantity between warehouses
   c. transaction.status = 'posted'
3. Response success or raises ValueError
```

### 12.3 Invoice Posting & Accounting Entry Creation

```
SalesService.post_invoice(invoice):
1. Validate: invoice.status == 'draft'
2. Filter items: product.product_type != 'service'
3. If storable items:
   a. Create StockTransaction(OUT)
   b. Create StockMovements (one per storable item)
   c. Call StockService.post_transaction()  [updates inventory]
4. Call AccountingService.create_sales_invoice_entry(invoice)  [creates GL entries]
5. Link invoice.journal_entry
6. Set invoice.status = 'posted'

AccountingService.create_sales_invoice_entry():
1. Create JournalEntry(journal_code=SAL, status=draft)
2. Add JournalItem(account=1003_Receivable, DR=total)
3. Add JournalItem(account=4001_Revenue, CR=total)
4. If has COGS items:
   a. Calculate total_cogs = SUM(qty × product.average_cost)
   b. Add JournalItem(account=5001_COGS, DR=total_cogs)
   c. Add JournalItem(account=1004_Inventory, CR=total_cogs)
5. Call entry.post()  [validates balance, sets status=posted]
```

---

## 13. QUERY OPTIMIZATION ISSUES

### 13.1 N+1 Query Problems Identified

#### **CRITICAL - StockService._update_average_cost_on_in()**
```python
# In loop of items:
total_qty = (
    StockBalance.objects.filter(product=product, company=product.company)
    .aggregate(total=Sum('quantity'))
    .get('total')
)
# Called once per item → N queries
```
**Fix**: Fetch all balances for product company in one query outside loop

#### **HIGH - AccountingService.create_sales_invoice_entry()**
```python
for item in invoice.items.select_related('product'):
    unit_cost = item.product.average_cost  # Already fetched
# Correct: select_related used ✓
```

#### **HIGH - JournalEntry.is_balanced property**
```python
@property
def is_balanced(self) -> bool:
    return self.total_debit == self.total_credit  # Calls total_debit getter
# total_debit calls self.items.aggregate(total=Sum('debit'))
# Queries every time property accessed
```
**Fix**: Cache after posting, or use @cached_property

#### **MODERATE - Account.current_balance property**
```python
@property
def current_balance(self) -> Decimal:
    if not self.is_postable:
        return Decimal('0.00')
    totals = self.journal_items.filter(
        entry__status='posted'
    ).aggregate(total_debit=Sum('debit'), total_credit=Sum('credit'))
    # One aggregate per account access
```
**Fix**: Use select_related('entry') in queryset, or cache balances separately

### 13.2 Missing Indexes

#### **Recommended Indexes** (not in Meta.indexes):

```python
# StockBalance
Index(fields=['warehouse', 'product'])  # For warehouse reports
Index(fields=['product'])  # For product stock check

# SalesInvoiceItem / PurchaseInvoiceItem
Index(fields=['invoice', 'product'])  # For line item lookups

# JournalItem
Index(fields=['account', 'entry__date'])  # For account statements

# StockTransaction
Index(fields=['source_warehouse', 'date'])  # For warehouse history

# Payment
Index(fields=['partner', 'date'])  # For partner statement
```

### 13.3 Inefficient Queries

#### **StockService.post_transaction() - Multiple selects per item**
```python
# For TRANSFER, each item does:
source_balance, _ = StockBalance.objects.select_for_update().get_or_create(...)
destination_balance, _ = StockBalance.objects.select_for_update().get_or_create(...)
# Can be 2 queries per item
```
**Fix**: Batch get_or_create or fetch all upfront with select_for_update

#### **SalesInvoiceItem._recalculate_invoice_total() - Called per item save**
```python
def save(self, *args, **kwargs):
    self.full_clean()
    super().save(*args, **kwargs)
    self.update_invoice_total()  # Aggregates entire invoice items

# If saving 10 items = 10 aggregates + 10 updates = 20 queries
```
**Fix**: Bulk operation or defer calculation until final save

### 13.4 Missing QuerySet Optimizations

#### **API ListViewSet for StockBalance**
```python
# Should use:
queryset = (
    StockBalance.objects
    .filter(is_deleted=False, company=user.company)
    .select_related('product', 'warehouse')
    .prefetch_related('warehouse__branch')
)
# Current likely doing N queries per warehouse access
```

#### **JournalEntry Detail View**
```python
# Should use:
.select_related('journal', 'company')\
.prefetch_related('items__account', 'items__partner')
# Correctly done in views.py ✓
```

---

## 14. ORPHAN MODELS & RELATIONSHIP ISSUES

### 14.1 Potential Orphan Records

#### **StockMovement without StockTransaction**
- FK StockTransaction(CASCADE) → No orphans possible
- Status: ✓ Safe

#### **SalesInvoiceItem without SalesInvoice**
- FK SalesInvoice(CASCADE) → No orphans possible
- Status: ✓ Safe

#### **JournalItem without JournalEntry**
- FK JournalEntry(CASCADE) → No orphans possible
- Status: ✓ Safe

#### **StockBalance orphaned if**
- Product deleted while StockBalance exists
- FK Product(PROTECT) → Cannot delete
- Warehouse deleted while balance exists
- FK Warehouse(PROTECT) → Cannot delete
- Status: ✓ Safe

#### **Unit orphan risk**
- FK on Product(PROTECT) → Cannot delete
- But Unit is global (not company-scoped)
- Status: ✓ Safe from deletion, but scoping issue exists

### 14.2 Dangling Foreign Keys

#### **Product.income_account / expense_account**
- FKs: Account(RESTRICT, nullable)
- If account deleted: Prevents deletion (RESTRICT)
- If set blank: Allows fallback to category accounts
- Status: ✓ Well-designed

#### **Journal.default_account**
- FK: Account(RESTRICT, nullable)
- If account deleted: Prevents deletion
- Status: ✓ Safe

#### **Warehouse.keeper (FK User)**
- FK: User(SET_NULL)
- If user deleted/soft-deleted: keeper = NULL
- Status: ✓ Safe

#### **StockTransaction.journal_entry**
- OneToOne: JournalEntry(SET_NULL)
- If entry deleted: transaction.journal_entry = NULL
- Status: ✓ Safe but inconsistent state

#### **SalesInvoice / PurchaseInvoice.journal_entry**
- OneToOne: JournalEntry(PROTECT)
- Cannot delete if linked
- **Issue**: Delete invoice → orphan journal entry (PROTECT prevents deletion)
- Status: ⚠️ Potential issue - consider CASCADE with reversal logic

#### **Payment.journal_entry**
- OneToOne: JournalEntry(SET_NULL)
- If entry deleted: payment.journal_entry = NULL
- Status: ✓ Safe but orphans accounting entry

### 14.3 Soft Delete Edge Cases

#### **StockTransaction soft-deleted but journal_entry linked**
- StockTransaction.is_deleted = True, journal_entry = active entry
- Query filtering out is_deleted=False won't show transaction
- But journal entry still shows (active)
- **Status**: Inconsistency - journal orphaned in soft-delete context

#### **Invoice soft-deleted but journal_entry linked**
- Same issue as above
- **Mitigation**: Could add transaction handler to soft-delete related journal entries

---

## 15. CRITICAL FINDINGS & RECOMMENDATIONS

### 15.1 High Priority Issues

#### 🔴 **Unit Model Not Company-Scoped**
- **Issue**: All companies share same units (global)
- **Risk**: Company A adds "kg", Company B can use same "kg"
- **Impact**: Medium (typically standardized)
- **Fix**: 
  ```python
  # Option 1: Add company FK
  company = ForeignKey(Company, on_delete=CASCADE, null=True)
  
  # Option 2: Create global units system (current design)
  # Just document that units are global
  ```

#### 🔴 **Category Model - Soft Delete Inconsistency**
- **Issue**: Category tree can become orphaned if parent is soft-deleted
- **Risk**: Reports showing deleted category hierarchies
- **Fix**: 
  ```python
  # Cascade soft-delete to children when parent deleted
  def soft_delete(self):
      self.subcategories.update(is_deleted=True, deleted_at=now())
      super().soft_delete()
  ```

#### 🔴 **N+1 in StockService Average Cost Calculation**
- **Issue**: One query per stock item during posting
- **Risk**: 100-item transaction = 100+ extra queries
- **Fix**: Pre-fetch all balances for product in single query

#### 🟡 **Invoice Journal Entry Orphaning on Delete**
- **Issue**: PROTECT prevents invoice deletion, but soft-delete bypasses it
- **Risk**: Soft-deleted invoice with active journal entry (data inconsistency)
- **Fix**: Override soft_delete() to cascade soft-delete to journal_entry

### 15.2 Medium Priority Issues

#### 🟡 **Missing Indexes on Frequently Filtered Columns**
- Warehouse, Product, Date filtering on stock queries
- Add indexes as listed in section 13.2

#### 🟡 **Cached Properties Used in Loops**
- `JournalEntry.is_balanced` called repeatedly
- **Fix**: Use `@cached_property` from `functools`

#### 🟡 **Decimal Precision Edge Case**
- ROUND_HALF_UP might cause rounding differences with other systems
- **Mitigation**: Document rounding policy; consider banker's rounding

#### 🟡 **Account Reconciliation Partner Validation**
- Validation enforces partner on reconcilable accounts
- But no corresponding constraint on database level
- **Fix**: Add database constraint or use validators more aggressively

### 15.3 Low Priority Issues

#### 🟢 **Service/Consumable Products**
- Can't create stock movements (validated)
- But StockBalance could theoretically exist
- **Status**: Acceptable - prevents accidental stock posting

#### 🟢 **Soft Delete Timestamp on Creation**
- deleted_at NULL until soft_delete() called
- **Status**: ✓ Correct

#### 🟢 **Partner Responsible User**
- FK User(SET_NULL) allows orphaning
- **Status**: ✓ Acceptable - user can be deactivated

---

## 16. SECURITY CONSIDERATIONS

### 16.1 Implemented Protections

✓ Company-level data isolation via queryset filtering  
✓ User.company enforced in all serializer validates  
✓ Soft-delete prevents accidental data loss  
✓ Audit logging captures all changes  
✓ FK constraints prevent referential integrity violations  

### 16.2 Potential Gaps

⚠️ **No explicit permission checks on Service methods**
- SalesService.post_invoice() called directly
- No permission verification inside
- **Mitigation**: API views should check permissions; services assume trusted caller

⚠️ **Decimal field injection**
- user.company auto-set in serializer
- But still validates user's company in validator
- **Status**: ✓ Protected

⚠️ **InjectionVulnerability in Sequence generation**
- Sequence keys user-supplied (company_id, branch_id)
- **Status**: ✓ Safe - coerced to int, used in f-string safely

---

## 17. DATABASE NORMALIZATION

### 17.1 Normalization Status

**Normal Form**: 3NF (mostly)

**Violations identified**: None critical

**Denormalization (intentional)**:
- StockBalance.reserved_quantity (denormalized from sale orders - not yet implemented)
- SalesInvoiceItem.line_total (denormalized, auto-calculated, editable=False)
- Product.average_cost (denormalized, cache of weighted average)
- **Status**: ✓ Acceptable - all recalculated on updates

### 17.2 Redundancy

- JournalEntry.company (redundant: via journal.company)
- SalesInvoice.company (redundant: via branch.company)
- **Status**: Acceptable - improves query performance

---

## 18. SUMMARY TABLE

| Aspect | Status | Risk | Notes |
|--------|--------|------|-------|
| Multi-company isolation | ✓ Implemented | Low | Filtered at API level |
| Status management | ✓ Implemented | Low | Draft→Posted lifecycle |
| Audit logging | ✓ Implemented | Low | AuditLog tracks all changes |
| Soft delete | ✓ Implemented | Medium | Orphaning possible on FK relationships |
| Auto-generated codes | ✓ Atomic generation | Low | Sequence model handles concurrency |
| Validation logic | ✓ Comprehensive | Low | clean() methods thorough |
| Accounting integration | ✓ Dual-entry | Low | Journal entries created automatically |
| Stock management | ✓ Atomic posting | Medium | N+1 query issue in average cost |
| Query optimization | ⚠️ Partial | Medium | Missing indexes, N+1 issues identified |
| Unit model scoping | ⚠️ Global | Medium | Not company-scoped |

---

## 19. APPENDIX: MODEL RELATIONSHIP DIAGRAM (Text)

```
Company (root)
├── Branch
│   ├── Warehouse
│   ├── SalesInvoice ─→ SalesInvoiceItem ─→ Product
│   ├── PurchaseInvoice ─→ PurchaseInvoiceItem ─→ Product
│   └── Payment
├── Product
│   ├── Category (tree)
│   ├── Unit (global)
│   ├── StockBalance ─→ Warehouse
│   └── StockMovement ─→ StockTransaction
├── StockTransaction
│   ├── Warehouse (source)
│   ├── Warehouse (destination)
│   ├── StockMovement (items)
│   └── JournalEntry
├── Partner (customer/supplier)
│   └── SalesInvoice / PurchaseInvoice / Payment
├── Account (tree)
│   ├── Journal (default)
│   ├── JournalEntry
│   ├── JournalItem
│   └── Product (income/expense)
├── Journal
│   └── JournalEntry (many)
└── User (multi-tenant)
    ├── company FK
    └── branch FK (optional)
```

---

**End of Analysis**
