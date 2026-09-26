from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models.account import Account
from apps.accounting.models.payment import Payment
from apps.core.models.company import Branch, Company
from apps.inventory.models import StockTransaction, Warehouse
from apps.partners.models import Partner
from apps.sales.models.sales_invoice import SalesInvoice
from apps.users.models import User
from apps.users.roles import (
    ROLE_ACCOUNTANT,
    ROLE_ACCOUNTING_MANAGER,
    ROLE_INVENTORY_MANAGER,
    ROLE_SALES_MANAGER,
    assign_role,
)


class AuthorizationFoundationAPITestCase(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        self.other_company = Company.objects.create(name="Other Company")
        self.other_branch = Branch.objects.create(
            company=self.other_company,
            name="Other Branch",
        )

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password",
            full_name="Test User",
            company=self.company,
            branch=self.branch,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password",
            full_name="Other User",
            company=self.other_company,
            branch=self.other_branch,
        )

        self.customer = Partner.objects.create(
            company=self.company,
            partner_type="customer",
            name="Customer A",
        )
        self.other_customer = Partner.objects.create(
            company=self.other_company,
            partner_type="customer",
            name="Other Customer",
        )
        self.cash_account = Account.objects.create(
            company=self.company,
            code="1002",
            name="Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
        )
        Account.objects.create(
            company=self.company,
            code="1003",
            name="Accounts Receivable",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
            allow_reconciliation=True,
        )
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse",
        )

    def test_cross_company_detail_access_is_blocked(self):
        invoice = SalesInvoice.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            customer=self.other_customer,
            status="draft",
        )
        assign_role(self.user, ROLE_SALES_MANAGER)
        self.client.force_authenticate(self.user)

        response = self.client.get(f"/api/sales/invoices/{invoice.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_sales_post_requires_sales_manager_role(self):
        invoice = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            status="draft",
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(f"/api/sales/invoices/{invoice.id}/post/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payment_post_and_cancel_require_accounting_roles(self):
        payment = Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("100.00"),
            status="draft",
        )
        self.client.force_authenticate(self.user)

        post_response = self.client.post(f"/api/accounting/payments/{payment.id}/post/")

        self.assertEqual(post_response.status_code, status.HTTP_403_FORBIDDEN)

        assign_role(self.user, ROLE_ACCOUNTANT)
        post_response = self.client.post(f"/api/accounting/payments/{payment.id}/post/")

        self.assertEqual(post_response.status_code, status.HTTP_200_OK)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "posted")

        cancel_response = self.client.post(f"/api/accounting/payments/{payment.id}/cancel/")

        self.assertEqual(cancel_response.status_code, status.HTTP_403_FORBIDDEN)

        assign_role(self.user, ROLE_ACCOUNTING_MANAGER)
        cancel_response = self.client.post(f"/api/accounting/payments/{payment.id}/cancel/")

        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)

    def test_stock_post_requires_inventory_manager_role(self):
        tx = StockTransaction.objects.create(
            company=self.company,
            transaction_type="IN",
            source_warehouse=self.warehouse,
            status="draft",
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(f"/api/inventory/stock-transactions/{tx.id}/post/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        assign_role(self.user, ROLE_INVENTORY_MANAGER)
        response = self.client.post(f"/api/inventory/stock-transactions/{tx.id}/post/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_general_ledger_requires_accounting_report_role(self):
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/accounting/reports/general-ledger/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        assign_role(self.user, ROLE_ACCOUNTANT)
        response = self.client.get("/api/accounting/reports/general-ledger/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
