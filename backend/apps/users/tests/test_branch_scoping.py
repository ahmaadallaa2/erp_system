from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models.payment import Payment
from apps.accounting.services.chart_of_accounts_seed import seed_standard_chart_of_accounts
from apps.accounting.services.payment_service import PaymentService
from apps.core.models.company import Branch, Company
from apps.inventory.models import Category, Product, StockBalance, Unit, Warehouse
from apps.partners.models import Partner
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.sales.models.sales_invoice import SalesInvoice
from apps.users.models import User
from apps.users.roles import (
    ROLE_ACCOUNTANT,
    ROLE_COMPANY_ADMIN,
    ROLE_SALES_MANAGER,
    assign_role,
)


class BranchScopingAPITestCase(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Branch A")
        self.other_branch = Branch.objects.create(company=self.company, name="Branch B")
        self.accounts = seed_standard_chart_of_accounts(self.company)

        self.user = User.objects.create_user(
            email="branch@example.com",
            password="password",
            full_name="Branch User",
            company=self.company,
            branch=self.branch,
        )
        assign_role(self.user, ROLE_SALES_MANAGER)

        self.company_user = User.objects.create_user(
            email="company@example.com",
            password="password",
            full_name="Company User",
            company=self.company,
            branch=self.branch,
        )
        assign_role(self.company_user, ROLE_COMPANY_ADMIN)

        self.customer = Partner.objects.create(
            company=self.company,
            partner_type="customer",
            name="Customer A",
        )
        self.supplier = Partner.objects.create(
            company=self.company,
            partner_type="supplier",
            name="Supplier A",
        )
        self.unit = Unit.objects.create(name="Piece", short_name="PCS")
        self.category = Category.objects.create(company=self.company, name="Main")
        self.product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Product A",
            product_type="storable",
            average_cost=Decimal("10.00"),
            sale_price=Decimal("20.00"),
        )
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Warehouse A",
        )
        self.other_warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.other_branch,
            name="Warehouse B",
        )

    def test_branch_user_cannot_list_other_branch_operational_records(self):
        own_sales = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
            status="posted",
        )
        other_sales = SalesInvoice.objects.create(
            company=self.company,
            branch=self.other_branch,
            customer=self.customer,
            warehouse=self.other_warehouse,
            total_amount=Decimal("200.00"),
            status="posted",
        )
        own_purchase = PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=self.supplier,
            warehouse=self.warehouse,
            total_amount=Decimal("50.00"),
            status="posted",
        )
        other_purchase = PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.other_branch,
            supplier=self.supplier,
            warehouse=self.other_warehouse,
            total_amount=Decimal("75.00"),
            status="posted",
        )
        own_payment = self.create_payment(self.branch)
        other_payment = self.create_payment(self.other_branch)

        self.client.force_authenticate(self.user)

        sales_response = self.client.get("/api/sales/invoices/")
        purchase_response = self.client.get("/api/purchases/invoices/")
        payment_response = self.client.get("/api/accounting/payments/")

        self.assert_ids(sales_response.data, includes=own_sales.id, excludes=other_sales.id)
        self.assert_ids(
            purchase_response.data,
            includes=own_purchase.id,
            excludes=other_purchase.id,
        )
        self.assert_ids(payment_response.data, includes=own_payment.id, excludes=other_payment.id)

    def test_branch_user_cannot_retrieve_post_or_cancel_other_branch_record(self):
        invoice = SalesInvoice.objects.create(
            company=self.company,
            branch=self.other_branch,
            customer=self.customer,
            warehouse=self.other_warehouse,
            status="draft",
        )
        self.client.force_authenticate(self.user)

        retrieve_response = self.client.get(f"/api/sales/invoices/{invoice.id}/")
        post_response = self.client.post(f"/api/sales/invoices/{invoice.id}/post/")
        cancel_response = self.client.post(f"/api/sales/invoices/{invoice.id}/cancel/")

        self.assertEqual(retrieve_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(post_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(cancel_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_company_wide_role_can_access_all_branches(self):
        own_sales = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="draft",
        )
        other_sales = SalesInvoice.objects.create(
            company=self.company,
            branch=self.other_branch,
            customer=self.customer,
            warehouse=self.other_warehouse,
            status="draft",
        )
        self.client.force_authenticate(self.company_user)

        response = self.client.get("/api/sales/invoices/")

        self.assert_ids(response.data, includes=own_sales.id, excludes=None)
        self.assert_ids(response.data, includes=other_sales.id, excludes=None)

    def test_dashboard_is_branch_scoped_for_branch_roles(self):
        SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            total_amount=Decimal("100.00"),
            status="posted",
        )
        SalesInvoice.objects.create(
            company=self.company,
            branch=self.other_branch,
            customer=self.customer,
            warehouse=self.other_warehouse,
            total_amount=Decimal("300.00"),
            status="posted",
        )

        self.client.force_authenticate(self.user)
        branch_response = self.client.get("/api/dashboard/summary/")
        self.client.force_authenticate(self.company_user)
        company_response = self.client.get("/api/dashboard/summary/")

        self.assertEqual(branch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(branch_response.data["total_sales"], Decimal("100.00"))
        self.assertEqual(company_response.data["total_sales"], Decimal("400.00"))

    def test_reports_are_branch_scoped_where_supported(self):
        StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal("5.00"),
        )
        StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.other_warehouse,
            quantity=Decimal("9.00"),
        )
        own_payment = self.create_payment(self.branch)
        other_payment = self.create_payment(self.other_branch)
        PaymentService.post_payment(own_payment)
        PaymentService.post_payment(other_payment)
        assign_role(self.user, ROLE_ACCOUNTANT)

        self.client.force_authenticate(self.user)
        warehouse_response = self.client.get("/api/inventory/reports/warehouse-balances/")
        ledger_response = self.client.get("/api/accounting/reports/general-ledger/")

        self.assertEqual(warehouse_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(warehouse_response.data), 1)
        self.assertEqual(
            warehouse_response.data[0]["warehouse_id"],
            str(self.warehouse.id),
        )
        self.assertEqual(ledger_response.status_code, status.HTTP_200_OK)
        ledger_entry_ids = {row["journal_entry_id"] for row in ledger_response.data}
        self.assertIn(str(own_payment.journal_entry_id), ledger_entry_ids)
        self.assertNotIn(str(other_payment.journal_entry_id), ledger_entry_ids)

    def create_payment(self, branch):
        return Payment.objects.create(
            company=self.company,
            branch=branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.accounts["1002"],
            amount=Decimal("25.00"),
            status="draft",
        )

    def assert_ids(self, rows, includes, excludes):
        row_ids = {row["id"] for row in rows}
        self.assertIn(str(includes), row_ids)
        if excludes is not None:
            self.assertNotIn(str(excludes), row_ids)
