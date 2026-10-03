from django.apps import apps as global_apps
from django.contrib.auth.models import Group
from django.db import DEFAULT_DB_ALIAS
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
    "accounting.payment.allocate": {
        ROLE_COMPANY_ADMIN,
        ROLE_ACCOUNTANT,
        ROLE_ACCOUNTING_MANAGER,
    },
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


VIEW = ("view",)
EDIT = ("view", "add", "change")


def _model_perms(app_label, model_names, actions):
    return {
        f"{app_label}.{action}_{model_name}"
        for model_name in model_names
        for action in actions
    }


_INVENTORY_MASTER = ("product", "category", "unit")
_INVENTORY_DOCUMENTS = ("stocktransaction", "stockmovement")
_SALES_MODELS = ("salesinvoice", "salesinvoiceitem")
_PURCHASE_MODELS = ("purchaseinvoice", "purchaseinvoiceitem")
_ACCOUNTING_CHART = ("account", "journal")
_ACCOUNTING_ENTRIES = ("journalentry", "journalitem")

_STOCK_LOOKUP = _model_perms("inventory", ("product", "warehouse", "stockbalance"), VIEW)

_BUSINESS_VIEW = (
    _model_perms("partners", ("partner",), VIEW)
    | _model_perms(
        "inventory",
        _INVENTORY_MASTER + ("warehouse", "stockbalance") + _INVENTORY_DOCUMENTS,
        VIEW,
    )
    | _model_perms("sales", _SALES_MODELS, VIEW)
    | _model_perms("purchases", _PURCHASE_MODELS, VIEW)
    | _model_perms("accounting", _ACCOUNTING_CHART + _ACCOUNTING_ENTRIES + ("payment",), VIEW)
)

_SALES_ROLE_PERMS = (
    _model_perms("partners", ("partner",), EDIT)
    | _STOCK_LOOKUP
    | _model_perms("sales", _SALES_MODELS, EDIT)
)
_PURCHASE_ROLE_PERMS = (
    _model_perms("partners", ("partner",), EDIT)
    | _STOCK_LOOKUP
    | _model_perms("purchases", _PURCHASE_MODELS, EDIT)
)
_INVENTORY_ROLE_PERMS = (
    _STOCK_LOOKUP
    | _model_perms("inventory", ("category", "unit"), VIEW)
    | _model_perms("inventory", _INVENTORY_DOCUMENTS, EDIT)
)
_ACCOUNTANT_PERMS = (
    _model_perms("accounting", _ACCOUNTING_CHART, VIEW)
    | _model_perms("accounting", _ACCOUNTING_ENTRIES + ("payment",), EDIT)
    | _model_perms("partners", ("partner",), VIEW)
    | _model_perms("sales", ("salesinvoice",), VIEW)
    | _model_perms("purchases", ("purchaseinvoice",), VIEW)
)
_AI_USER_PERMS = (
    _model_perms("ai_assistant", ("document",), ("view", "add"))
    | _model_perms("ai_assistant", ("documentchunk",), VIEW)
)

# Django model permissions per role (they drive the admin site only; API
# actions are gated by ROLE_ACTIONS). No role gets delete or users/auth
# permissions: deletion and user management stay with superusers.
ROLE_MODEL_PERMISSIONS = {
    ROLE_COMPANY_ADMIN: (
        _model_perms("partners", ("partner",), EDIT)
        | _model_perms("inventory", _INVENTORY_MASTER + ("warehouse",) + _INVENTORY_DOCUMENTS, EDIT)
        | _model_perms("inventory", ("stockbalance",), VIEW)
        | _model_perms("sales", _SALES_MODELS, EDIT)
        | _model_perms("purchases", _PURCHASE_MODELS, EDIT)
        | _model_perms("accounting", _ACCOUNTING_CHART + _ACCOUNTING_ENTRIES + ("payment",), EDIT)
        | _model_perms("core", ("company",), VIEW)
        | _model_perms("core", ("branch", "fiscalyear"), EDIT)
        | _model_perms("core", ("auditlog",), VIEW)
    ),
    ROLE_BRANCH_MANAGER: (
        _BUSINESS_VIEW
        | _model_perms("partners", ("partner",), EDIT)
        | _model_perms("sales", _SALES_MODELS, EDIT)
        | _model_perms("purchases", _PURCHASE_MODELS, EDIT)
        | _model_perms("inventory", _INVENTORY_DOCUMENTS, EDIT)
    ),
    ROLE_SALES_USER: _SALES_ROLE_PERMS,
    ROLE_SALES_MANAGER: _SALES_ROLE_PERMS,
    ROLE_PURCHASE_USER: _PURCHASE_ROLE_PERMS,
    ROLE_PURCHASE_MANAGER: _PURCHASE_ROLE_PERMS,
    ROLE_INVENTORY_USER: _INVENTORY_ROLE_PERMS,
    ROLE_INVENTORY_MANAGER: (
        _INVENTORY_ROLE_PERMS
        | _model_perms("inventory", _INVENTORY_MASTER + ("warehouse",), EDIT)
    ),
    ROLE_ACCOUNTANT: _ACCOUNTANT_PERMS,
    ROLE_ACCOUNTING_MANAGER: (
        _ACCOUNTANT_PERMS
        | _model_perms("accounting", _ACCOUNTING_CHART, EDIT)
        | _model_perms("core", ("fiscalyear",), EDIT)
    ),
    ROLE_AUDITOR: (
        _BUSINESS_VIEW
        | _model_perms("core", ("company", "branch", "fiscalyear", "auditlog"), VIEW)
    ),
    ROLE_AI_USER: _AI_USER_PERMS,
    ROLE_AI_ADMIN: _AI_USER_PERMS | _model_perms("ai_assistant", ("document",), ("change",)),
}


def sync_role_groups(app_label=None, using=DEFAULT_DB_ALIAS, apps=global_apps):
    """
    Create missing role groups and grant their mapped model permissions.

    Pass `app_label` to grant only that app's permissions. Permissions are only
    added, never removed, so manual grants made in the admin are kept.
    Returns the number of groups created.
    """
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")

    groups = {
        group.name: group
        for group in group_model.objects.using(using).filter(name__in=SYSTEM_ROLES)
    }
    missing = [name for name in SYSTEM_ROLES if name not in groups]
    for name in missing:
        groups[name] = group_model.objects.using(using).create(name=name)

    wanted = {
        role: {
            tuple(perm.split(".", 1))
            for perm in perms
            if app_label is None or perm.split(".", 1)[0] == app_label
        }
        for role, perms in ROLE_MODEL_PERMISSIONS.items()
    }
    needed = set().union(*wanted.values())
    if not needed:
        return len(missing)

    permissions = {
        (perm.content_type.app_label, perm.codename): perm
        for perm in permission_model.objects.using(using)
        .filter(
            content_type__app_label__in={label for label, _ in needed},
            codename__in={codename for _, codename in needed},
        )
        .select_related("content_type")
    }

    for role, keys in wanted.items():
        role_permissions = [permissions[key] for key in keys if key in permissions]
        if role_permissions:
            groups[role].permissions.add(*role_permissions)

    return len(missing)


def create_default_groups():
    return sync_role_groups()


# Role group every user of a given user_type always gets.
USER_TYPE_DEFAULT_ROLES = {
    "company_admin": ROLE_COMPANY_ADMIN,
    "branch_manager": ROLE_BRANCH_MANAGER,
}


def set_user_roles(user, role_names):
    """Replace the user's ERP role groups; non-ERP groups are left untouched."""
    unknown = set(role_names) - set(SYSTEM_ROLES)
    if unknown:
        raise ValueError(f"Unknown ERP roles: {', '.join(sorted(unknown))}")

    user.groups.remove(*user.groups.filter(name__in=SYSTEM_ROLES).exclude(name__in=role_names))
    for role_name in role_names:
        assign_role(user, role_name)


def is_system_admin(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or getattr(user, "user_type", None) == "system_admin"


def is_company_admin(user):
    if not user or not user.is_authenticated or not getattr(user, "company_id", None):
        return False
    if getattr(user, "user_type", None) == "company_admin":
        return True
    return ROLE_COMPANY_ADMIN in user_role_names(user)


def can_manage_users(user):
    return is_system_admin(user) or is_company_admin(user)


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
