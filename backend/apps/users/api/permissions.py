from rest_framework.permissions import BasePermission

from apps.users.roles import (
    can_manage_users,
    has_company_wide_access,
    has_erp_action_permission,
    is_system_admin,
    user_can_access_branch_object,
)


class IsCompanyMember(BasePermission):
    message = "Authenticated user must belong to a company."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.company_id)

    def has_object_permission(self, request, view, obj):
        obj_company_id = getattr(obj, "company_id", None)

        if obj_company_id is None and hasattr(obj, "company"):
            obj_company_id = getattr(obj.company, "id", None)

        if obj_company_id is None and hasattr(obj, "invoice"):
            obj_company_id = getattr(obj.invoice, "company_id", None)

        if obj_company_id is None and hasattr(obj, "transaction"):
            obj_company_id = getattr(obj.transaction, "company_id", None)

        return obj_company_id is None or obj_company_id == request.user.company_id


class HasBranchAccess(BasePermission):
    message = "User does not have access to this branch."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.company_id)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if has_company_wide_access(user):
            return True

        return user_can_access_branch_object(user, obj)


class HasERPActionPermission(BasePermission):
    action = None
    message = "User does not have permission to perform this ERP action."

    def has_permission(self, request, view):
        return has_erp_action_permission(request.user, self.action)


class CanPostSalesInvoice(HasERPActionPermission):
    action = "sales.invoice.post"


class CanCancelSalesInvoice(HasERPActionPermission):
    action = "sales.invoice.cancel"


class CanPostPurchaseInvoice(HasERPActionPermission):
    action = "purchases.invoice.post"


class CanCancelPurchaseInvoice(HasERPActionPermission):
    action = "purchases.invoice.cancel"


class CanPostPayment(HasERPActionPermission):
    action = "accounting.payment.post"


class CanCancelPayment(HasERPActionPermission):
    action = "accounting.payment.cancel"


class CanAllocatePayment(HasERPActionPermission):
    action = "accounting.payment.allocate"


class CanPostStockTransaction(HasERPActionPermission):
    action = "inventory.stock_transaction.post"


class CanViewAccountingReports(HasERPActionPermission):
    action = "accounting.reports.view"


class CanManageUsers(BasePermission):
    """System admins manage every user; company admins only their company's
    users, excluding superusers and system admins."""

    message = "Only system or company administrators can manage users."

    def has_permission(self, request, view):
        return can_manage_users(request.user)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_system_admin(user):
            return True
        if obj.is_superuser or obj.user_type == "system_admin":
            return False
        return obj.company_id == user.company_id
