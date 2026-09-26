from rest_framework.permissions import BasePermission

from apps.users.roles import (
    has_company_wide_access,
    has_erp_action_permission,
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


class CanPostStockTransaction(HasERPActionPermission):
    action = "inventory.stock_transaction.post"


class CanViewAccountingReports(HasERPActionPermission):
    action = "accounting.reports.view"
