from decimal import Decimal

from django.db.models import Count, F, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounting.models.payment import Payment
from apps.inventory.models.stock_balance import StockBalance
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.sales.models.sales_invoice import SalesInvoice
from apps.users.api.permissions import IsCompanyMember
from apps.users.roles import scope_queryset_to_user_branch


class DashboardSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.user.company

        if not company:
            return Response(self.empty_summary())

        sales = scope_queryset_to_user_branch(
            SalesInvoice.objects.filter(company=company, status="posted"),
            request.user,
            "branch_id",
        )
        purchases = scope_queryset_to_user_branch(
            PurchaseInvoice.objects.filter(company=company, status="posted"),
            request.user,
            "branch_id",
        )
        inbound = scope_queryset_to_user_branch(
            Payment.objects.filter(
                company=company,
                status="posted",
                payment_type="inbound",
            ),
            request.user,
            "branch_id",
        )
        outbound = scope_queryset_to_user_branch(
            Payment.objects.filter(
                company=company,
                status="posted",
                payment_type="outbound",
            ),
            request.user,
            "branch_id",
        )
        stock_balances = scope_queryset_to_user_branch(
            StockBalance.objects.filter(company=company),
            request.user,
            "warehouse__branch_id",
        )

        total_sales = self.sum_amount(sales, "total_amount")
        total_purchases = self.sum_amount(purchases, "total_amount")
        inbound_payments = self.sum_amount(inbound, "amount")
        outbound_payments = self.sum_amount(outbound, "amount")

        data = {
            "total_sales": total_sales,
            "total_purchases": total_purchases,
            "inventory_items": stock_balances.aggregate(
                total=Count("product", distinct=True)
            )["total"]
            or 0,
            "inventory_quantity": self.sum_amount(stock_balances, "quantity"),
            "customers_receivable": total_sales - inbound_payments,
            "suppliers_payable": total_purchases - outbound_payments,
            "low_stock_products": stock_balances.exclude(
                reorder_point__isnull=True
            )
            .filter(quantity__lte=F("reorder_point"))
            .count(),
        }

        return Response(data)

    @staticmethod
    def sum_amount(queryset, field_name):
        return queryset.aggregate(total=Sum(field_name))["total"] or Decimal("0.00")

    @staticmethod
    def empty_summary():
        zero = Decimal("0.00")
        return {
            "total_sales": zero,
            "total_purchases": zero,
            "inventory_items": 0,
            "inventory_quantity": zero,
            "customers_receivable": zero,
            "suppliers_payable": zero,
            "low_stock_products": 0,
        }
