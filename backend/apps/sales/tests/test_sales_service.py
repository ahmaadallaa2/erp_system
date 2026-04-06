from decimal import Decimal

from django.test import TestCase

from apps.core.models.company import Company, Branch
from apps.inventory.models import Category, Unit, Product, Warehouse, StockBalance
from apps.partners.models import Partner
from apps.sales.models.sales_invoice import SalesInvoice
from apps.sales.models.sales_invoice_item import SalesInvoiceItem
from apps.sales.services.sales_service import SalesService


class SalesServiceTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(
            company=self.company,
            name="Main Branch"
        )
        self.category = Category.objects.create(
            company=self.company,
            name="Electronics"
        )
        self.unit = Unit.objects.create(
            name="Piece",
            short_name="PCS"
        )
        self.product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Laptop",
            product_type="storable",
            cost_price=Decimal("100.00"),
            average_cost=Decimal("100.00"),
            sale_price=Decimal("150.00"),
        )
        self.service_product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Maintenance Service",
            product_type="service",
            cost_price=Decimal("0.00"),
            average_cost=Decimal("0.00"),
            sale_price=Decimal("50.00"),
        )
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse"
        )
        self.customer = Partner.objects.create(
            company=self.company,
            partner_type="customer",
            name="Customer A"
        )

        StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal("10.00"),
            reserved_quantity=Decimal("0.00"),
        )

    def test_post_sales_invoice_reduces_stock_and_updates_status(self):
        invoice = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="draft",
        )

        SalesInvoiceItem.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=Decimal("3.00"),
            unit_price=Decimal("150.00"),
        )

        stock_tx = SalesService.post_invoice(invoice)

        invoice.refresh_from_db()
        balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(invoice.status, "posted")
        self.assertEqual(stock_tx.transaction_type, "OUT")
        self.assertEqual(balance.quantity, Decimal("7.00"))

    def test_post_sales_invoice_fails_when_stock_not_enough(self):
        invoice = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="draft",
        )

        SalesInvoiceItem.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=Decimal("20.00"),
            unit_price=Decimal("150.00"),
        )

        with self.assertRaises(ValueError):
            SalesService.post_invoice(invoice)

    def test_service_items_do_not_create_stock_movement(self):
        invoice = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="draft",
        )

        SalesInvoiceItem.objects.create(
            invoice=invoice,
            product=self.service_product,
            quantity=Decimal("2.00"),
            unit_price=Decimal("50.00"),
        )

        stock_tx = SalesService.post_invoice(invoice)

        invoice.refresh_from_db()

        self.assertEqual(invoice.status, "posted")
        self.assertIsNone(stock_tx)

    def test_cannot_post_empty_sales_invoice(self):
        invoice = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="draft",
        )

        with self.assertRaises(ValueError):
            SalesService.post_invoice(invoice)

    def test_cannot_post_non_draft_sales_invoice(self):
        invoice = SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status="posted",
        )

        with self.assertRaises(ValueError):
            SalesService.post_invoice(invoice)