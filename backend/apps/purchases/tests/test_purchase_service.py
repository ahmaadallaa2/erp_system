from decimal import Decimal

from django.test import TestCase

from apps.accounting.models import Account, JournalEntry
from apps.accounting.services.chart_of_accounts_seed import (
    seed_standard_chart_of_accounts,
)
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
        self.accounts = seed_standard_chart_of_accounts(self.company)
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
        self.assertIsNotNone(invoice.journal_entry_id)
        self.assertEqual(stock_tx.transaction_type, "IN")
        self.assertEqual(balance.quantity, Decimal("10.00"))
        self.assertEqual(self.product.average_cost, Decimal("120.00"))

    def test_post_purchase_invoice_creates_accounting_entry(self):
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

        PurchaseService.post_invoice(invoice)
        invoice.refresh_from_db()

        entry = invoice.journal_entry
        self.assertIsNotNone(entry)
        self.assertEqual(entry.status, "posted")
        self.assertEqual(entry.total_debit, entry.total_credit)
        self.assertEqual(entry.total_debit, invoice.total_amount)

        inventory_line = entry.items.get(account=self.accounts["1004"])
        payable_line = entry.items.get(account=self.accounts["2001"])

        self.assertEqual(inventory_line.debit, invoice.total_amount)
        self.assertIsNone(inventory_line.partner)
        self.assertEqual(payable_line.credit, invoice.total_amount)
        self.assertEqual(payable_line.partner, self.supplier)

    def test_purchase_invoice_accounting_includes_shipping_and_clearance(self):
        invoice = PurchaseInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            supplier=self.supplier,
            warehouse=self.warehouse,
            status="draft",
            shipping_cost=Decimal("20.00"),
            clearance_cost=Decimal("10.00"),
            commission_percentage=Decimal("5.00"),
        )

        PurchaseInvoiceItem.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=Decimal("2.00"),
            unit_price=Decimal("120.00"),
        )

        PurchaseService.post_invoice(invoice)
        invoice.refresh_from_db()

        self.assertEqual(invoice.total_amount, Decimal("270.00"))
        inventory_line = invoice.journal_entry.items.get(account=self.accounts["1004"])
        payable_line = invoice.journal_entry.items.get(account=self.accounts["2001"])

        self.assertEqual(inventory_line.debit, Decimal("270.00"))
        self.assertEqual(payable_line.credit, Decimal("270.00"))

    def test_duplicate_posting_does_not_create_duplicate_entries(self):
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
            quantity=Decimal("2.00"),
            unit_price=Decimal("120.00"),
        )

        PurchaseService.post_invoice(invoice)
        invoice.refresh_from_db()
        first_entry_id = invoice.journal_entry_id
        entry_count = JournalEntry.objects.count()

        with self.assertRaises(ValueError):
            PurchaseService.post_invoice(invoice)

        invoice.refresh_from_db()
        self.assertEqual(invoice.journal_entry_id, first_entry_id)
        self.assertEqual(JournalEntry.objects.count(), entry_count)

    def test_accounting_failure_rolls_back_stock_and_invoice_status(self):
        Account.objects.filter(
            company=self.company,
            code="2001",
            is_deleted=False,
        ).delete()

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
            quantity=Decimal("5.00"),
            unit_price=Decimal("120.00"),
        )

        with self.assertRaises(Account.DoesNotExist):
            PurchaseService.post_invoice(invoice)

        invoice.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(invoice.status, "draft")
        self.assertIsNone(invoice.journal_entry_id)
        self.assertFalse(
            StockBalance.objects.filter(
                company=self.company,
                product=self.product,
                warehouse=self.warehouse,
            ).exists()
        )
        self.assertEqual(self.product.average_cost, Decimal("100.00"))

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
