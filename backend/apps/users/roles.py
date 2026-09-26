from django.contrib.auth.models import Group
from django.db.models import Q


ROLE_COMPANY_ADMIN = "CompanyAdmin"
ROLE_BRANCH_MANAGER = "BranchManager"
ROLE_SALES_USER = "SalesUser"
ROLE_SALES_MANAGER = "SalesManager"
ROLE_PURCHASE_USER = "PurchaseUser"
ROLE_PURCHASE_MANAGER = "PurchaseManager"
ROLE_INVENTORY_USER = "InventoryUser"
ROLE_INVENTORY_MANAGER = "InventoryManager"
ROLE_ACCOUNTANT = "Accountant"
ROLE_ACCOUNTING_MANAGER = "AccountingManager"
ROLE_AUDITOR = "Auditor"
ROLE_AI_USER = "AIUser"
ROLE_AI_ADMIN = "AIAdmin"

COMPANY_WIDE_ROLES = {
    ROLE_COMPANY_ADMIN,
    ROLE_ACCOUNTING_MANAGER,
    ROLE_AUDITOR,
}


SYSTEM_ROLES = [
    ROLE_COMPANY_ADMIN,
    ROLE_BRANCH_MANAGER,
    ROLE_SALES_USER,
    ROLE_SALES_MANAGER,
    ROLE_PURCHASE_USER,
    ROLE_PURCHASE_MANAGER,
    ROLE_INVENTORY_USER,
    ROLE_INVENTORY_MANAGER,
    ROLE_ACCOUNTANT,
    ROLE_ACCOUNTING_MANAGER,
    ROLE_AUDITOR,
    ROLE_AI_USER,
    ROLE_AI_ADMIN,
]


ROLE_ACTIONS = {
    "sales.invoice.post": {ROLE_COMPANY_ADMIN, ROLE_SALES_MANAGER},
    "sales.invoice.cancel": {
        ROLE_COMPANY_ADMIN,
        ROLE_SALES_MANAGER,
        ROLE_ACCOUNTING_MANAGER,
    },
    "purchases.invoice.post": {ROLE_COMPANY_ADMIN, ROLE_PURCHASE_MANAGER},
    "purchases.invoice.cancel": {
        ROLE_COMPANY_ADMIN,
        ROLE_PURCHASE_MANAGER,
        ROLE_ACCOUNTING_MANAGER,
    },
    "accounting.payment.post": {
        ROLE_COMPANY_ADMIN,
        ROLE_ACCOUNTANT,
        ROLE_ACCOUNTING_MANAGER,
    },
    "accounting.payment.cancel": {ROLE_COMPANY_ADMIN, ROLE_ACCOUNTING_MANAGER},
    "inventory.stock_transaction.post": {
        ROLE_COMPANY_ADMIN,
        ROLE_INVENTORY_MANAGER,
    },
    "accounting.reports.view": {
        ROLE_COMPANY_ADMIN,
        ROLE_ACCOUNTANT,
        ROLE_ACCOUNTING_MANAGER,
        ROLE_AUDITOR,
    },
}


def create_default_groups():
    created_count = 0
    for role_name in SYSTEM_ROLES:
        _, created = Group.objects.get_or_create(name=role_name)
        if created:
            created_count += 1
    return created_count


def user_role_names(user):
    if not user or not user.is_authenticated:
        return set()
    return set(user.groups.values_list("name", flat=True))


def has_role(user, *role_names):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if getattr(user, "user_type", None) in {"system_admin", "company_admin"}:
        return True
    return bool(user_role_names(user).intersection(role_names))


def has_company_wide_access(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if getattr(user, "user_type", None) in {"system_admin", "company_admin"}:
        return True
    return bool(user_role_names(user).intersection(COMPANY_WIDE_ROLES))


def branch_filter_q(user, *branch_paths):
    if has_company_wide_access(user):
        return Q()

    if not getattr(user, "branch_id", None):
        return Q(pk__in=[])

    query = Q()
    for branch_path in branch_paths:
        query |= Q(**{branch_path: user.branch_id})
    return query


def scope_queryset_to_user_branch(queryset, user, *branch_paths):
    return queryset.filter(branch_filter_q(user, *branch_paths)).distinct()


def user_can_access_branch_id(user, branch_id):
    if branch_id is None:
        return True
    if has_company_wide_access(user):
        return True
    return bool(getattr(user, "branch_id", None) and branch_id == user.branch_id)


def object_branch_ids(obj):
    branch_ids = []

    branch_id = getattr(obj, "branch_id", None)
    if branch_id:
        branch_ids.append(branch_id)

    invoice = getattr(obj, "invoice", None)
    if invoice and getattr(invoice, "branch_id", None):
        branch_ids.append(invoice.branch_id)

    transaction = getattr(obj, "transaction", None)
    if transaction:
        branch_ids.extend(object_branch_ids(transaction))

    source_warehouse = getattr(obj, "source_warehouse", None)
    if source_warehouse and getattr(source_warehouse, "branch_id", None):
        branch_ids.append(source_warehouse.branch_id)

    destination_warehouse = getattr(obj, "destination_warehouse", None)
    if destination_warehouse and getattr(destination_warehouse, "branch_id", None):
        branch_ids.append(destination_warehouse.branch_id)

    warehouse = getattr(obj, "warehouse", None)
    if warehouse and getattr(warehouse, "branch_id", None):
        branch_ids.append(warehouse.branch_id)

    linked_payment = getattr(obj, "linked_payment", None)
    if linked_payment and getattr(linked_payment, "branch_id", None):
        branch_ids.append(linked_payment.branch_id)

    sales_invoice = getattr(obj, "sales_invoice", None)
    if sales_invoice and getattr(sales_invoice, "branch_id", None):
        branch_ids.append(sales_invoice.branch_id)

    purchase_invoice = getattr(obj, "purchase_invoice", None)
    if purchase_invoice and getattr(purchase_invoice, "branch_id", None):
        branch_ids.append(purchase_invoice.branch_id)

    stock_transaction = getattr(obj, "stock_transaction", None)
    if stock_transaction:
        branch_ids.extend(object_branch_ids(stock_transaction))

    return branch_ids


def user_can_access_branch_object(user, obj):
    if has_company_wide_access(user):
        return True

    branch_ids = object_branch_ids(obj)
    if not branch_ids:
        return True

    user_branch_id = getattr(user, "branch_id", None)
    return bool(user_branch_id and user_branch_id in branch_ids)


def has_erp_action_permission(user, action):
    allowed_roles = ROLE_ACTIONS.get(action, set())
    return has_role(user, *allowed_roles)


def assign_role(user, role_name):
    if role_name not in SYSTEM_ROLES:
        raise ValueError(f"Unknown ERP role: {role_name}")

    group, _ = Group.objects.get_or_create(name=role_name)
    user.groups.add(group)
    return group
