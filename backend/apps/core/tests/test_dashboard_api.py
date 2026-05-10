from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models.account import Account
from apps.accounting.models.payment import Payment
from apps.core.models.company import Branch, Company
from apps.inventory.models import Category, Product, StockBalance, Unit, Warehouse
from apps.partners.models import Partner
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.sales.models.sales_invoice import SalesInvoice
from apps.users.models import User


class DashboardSummaryAPITestCase(APITestCase):
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
        self.other_customer = Partner.objects.create(
            company=self.other_company,
            partner_type="customer",
            name="Other Customer",
        )
        self.other_supplier = Partner.objects.create(
            company=self.other_company,
            partner_type="supplier",
            name="Other Supplier",
        )

        self.unit = Unit.objects.create(name="Piece", short_name="PCS")
        self.category = Category.objects.create(company=self.company, name="Main")
        self.other_category = Category.objects.create(
            company=self.other_company,
            name="Other",
        )
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse",
        )
        self.other_warehouse = Warehouse.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            name="Other Warehouse",
        )
        self.product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Product A",
        )
        self.product_b = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Product B",
        )
        self.other_product = Product.objects.create(
            company=self.other_company,
            category=self.other_category,
            unit=self.unit,
            name="Other Product",
        )

        self.cash_account = Account.objects.create(
            company=self.company,
            code="1002",
            name="Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
        )
        self.other_cash_account = Account.objects.create(
            company=self.other_company,
            code="1002",
            name="Other Cash",
            account_type="asset",
            normal_balance="debit",
            is_postable=True,
        )

        self.url = "/api/dashboard/summary/"

    def test_auth_required(self):
        response = self.client.get(self.url)

        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_empty_database_returns_zeros(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "total_sales": Decimal("0.00"),
                "total_purchases": Decimal("0.00"),
                "inventory_items": 0,
                "inventory_quantity": Decimal("0.00"),
                "customers_receivable": Decimal("0.00"),
                "suppliers_payable": Decimal("0.00"),
                "low_stock_products": 0,
            },
        )

    def test_summary_values_aggregate_correctly(self):
        self.client.force_authenticate(self.user)
        self.create_company_data()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_sales"], Decimal("500.00"))
        self.assertEqual(response.data["total_purchases"], Decimal("300.00"))
        self.assertEqual(response.data["inventory_items"], 2)
        self.assertEqual(response.data["inventory_quantity"], Decimal("13.00"))
        self.assertEqual(response.data["customers_receivable"], Decimal("350.00"))
        self.assertEqual(response.data["suppliers_payable"], Decimal("200.00"))
        self.assertEqual(response.data["low_stock_products"], 1)

    def test_company_scoping_works(self):
        self.client.force_authenticate(self.user)
        self.create_company_data()
        self.create_other_company_data()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_sales"], Decimal("500.00"))
        self.assertEqual(response.data["total_purchases"], Decimal("300.00"))
        self.assertEqual(response.data["inventory_items"], 2)
        self.assertEqual(response.data["inventory_quantity"], Decimal("13.00"))

    def create_company_data(self):
        SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="posted",
            total_amount=Decimal("500.00"),
        )
        SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="draft",
            total_amount=Decimal("999.00"),
        )
        PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="posted",
            total_amount=Decimal("300.00"),
        )
        Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("150.00"),
            status="posted",
        )
        Payment.objects.create(
            company=self.company,
            branch=self.branch,
            partner=self.supplier,
            payment_type="outbound",
            payment_method="cash",
            account=self.cash_account,
            amount=Decimal("100.00"),
            status="posted",
        )
        StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal("3.00"),
            reorder_point=Decimal("5.00"),
        )
        StockBalance.objects.create(
            company=self.company,
            product=self.product_b,
            warehouse=self.warehouse,
            quantity=Decimal("10.00"),
            reorder_point=Decimal("5.00"),
        )

    def create_other_company_data(self):
        SalesInvoice.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            customer=self.other_customer,
            warehouse=self.other_warehouse,
            status="posted",
            total_amount=Decimal("700.00"),
        )
        PurchaseInvoice.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            supplier=self.other_supplier,
            warehouse=self.other_warehouse,
            status="posted",
            total_amount=Decimal("400.00"),
        )
        Payment.objects.create(
            company=self.other_company,
            branch=self.other_branch,
            partner=self.other_customer,
            payment_type="inbound",
            payment_method="cash",
            account=self.other_cash_account,
            amount=Decimal("200.00"),
            status="posted",
        )
        StockBalance.objects.create(
            company=self.other_company,
            product=self.other_product,
            warehouse=self.other_warehouse,
            quantity=Decimal("99.00"),
            reorder_point=Decimal("100.00"),
        )
