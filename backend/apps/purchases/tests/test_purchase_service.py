from decimal import Decimal

from django.test import TestCase

from apps.core.models.company import Company, Branch
from apps.inventory.models import Category, Unit, Product, Warehouse, StockBalance
from apps.partners.models import Partner
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.purchases.models.purchase_invoice_item import PurchaseInvoiceItem
from apps.purchases.services.purchase_service import PurchaseService


class PurchaseServiceTestCase(TestCase):
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
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse"
        )
        self.supplier = Partner.objects.create(
            company=self.company,
            partner_type="supplier",
            name="Supplier A"
        )

    def test_post_purchase_invoice_creates_stock_and_updates_status(self):
        invoice = PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="draft",
        )

        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=Decimal("10.00"),
            unit_price=Decimal("120.00"),
        )

        stock_tx = PurchaseService.post_invoice(invoice)

        invoice.refresh_from_db()
        self.product.refresh_from_db()

        balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(invoice.status, "posted")
        self.assertEqual(stock_tx.transaction_type, "IN")
        self.assertEqual(balance.quantity, Decimal("10.00"))
        self.assertEqual(self.product.average_cost, Decimal("120.00"))

    def test_cannot_post_empty_purchase_invoice(self):
        invoice = PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="draft",
        )

        with self.assertRaises(ValueError):
            PurchaseService.post_invoice(invoice)

    def test_cannot_post_non_draft_purchase_invoice(self):
        invoice = PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="posted",
        )

        with self.assertRaises(ValueError):
            PurchaseService.post_invoice(invoice)