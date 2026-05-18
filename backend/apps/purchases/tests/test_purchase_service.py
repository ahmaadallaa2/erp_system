from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounting.models import Account, JournalEntry
from apps.accounting.services.chart_of_accounts_seed import (
    seed_standard_chart_of_accounts,
)
from apps.core.models.company import Company, Branch
from apps.inventory.models import (
    Category,
    Product,
    StockBalance,
    StockTransaction,
    Unit,
    Warehouse,
)
from apps.partners.models import Partner
from apps.purchases.models.purchase_invoice import PurchaseInvoice
from apps.purchases.models.purchase_invoice_item import PurchaseInvoiceItem
from apps.purchases.services.purchase_service import PurchaseService
from apps.users.models import User


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

        stock_tx = PurchaseService.post_invoice(invoice)
        invoice.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(invoice.total_amount, Decimal("270.00"))
        inventory_line = invoice.journal_entry.items.get(account=self.accounts["1004"])
        payable_line = invoice.journal_entry.items.get(account=self.accounts["2001"])
        movement = stock_tx.items.get(product=self.product)
        posted_stock_value = movement.quantity * movement.unit_cost

        # commission_percentage is intentionally not included in total_amount yet.
        self.assertEqual(inventory_line.debit, Decimal("270.00"))
        self.assertEqual(payable_line.credit, Decimal("270.00"))
        self.assertEqual(movement.unit_cost, Decimal("135.00"))
        self.assertEqual(posted_stock_value, inventory_line.debit)
        self.assertEqual(self.product.average_cost, Decimal("135.00"))
        self.assertEqual(invoice.journal_entry.total_debit, invoice.journal_entry.total_credit)

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

    def test_cancel_posted_invoice_restores_stock_and_creates_reversal_journal(self):
        invoice = self.create_invoice(quantity=Decimal("5.00"))
        original_stock_tx = PurchaseService.post_invoice(invoice)
        invoice.refresh_from_db()
        original_journal_id = invoice.journal_entry_id

        result = PurchaseService.cancel_invoice(invoice)

        invoice.refresh_from_db()
        balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(invoice.status, "cancelled")
        self.assertEqual(invoice.journal_entry_id, original_journal_id)
        self.assertEqual(balance.quantity, Decimal("0.00"))

        original_entry = JournalEntry.objects.get(id=original_journal_id)
        self.assertEqual(original_entry.status, "posted")

        reversal_entry = result["journal_entry"]
        self.assertNotEqual(reversal_entry.id, original_journal_id)
        self.assertEqual(reversal_entry.status, "posted")
        self.assertEqual(reversal_entry.reference, f"REV-{invoice.invoice_number}")
        self.assertEqual(reversal_entry.total_debit, reversal_entry.total_credit)

        inventory_line = reversal_entry.items.get(account=self.accounts["1004"])
        payable_line = reversal_entry.items.get(account=self.accounts["2001"])

        self.assertEqual(inventory_line.credit, Decimal("600.00"))
        self.assertIsNone(inventory_line.partner)
        self.assertEqual(payable_line.debit, Decimal("600.00"))
        self.assertEqual(payable_line.partner, self.supplier)

        reversal_stock_tx = result["stock_transaction"]
        self.assertEqual(reversal_stock_tx.transaction_type, "OUT")
        self.assertEqual(reversal_stock_tx.status, "posted")
        self.assertEqual(reversal_stock_tx.reference, f"REV-{invoice.invoice_number}")
        self.assertEqual(reversal_stock_tx.items.get().quantity, Decimal("5.00"))
        self.assertEqual(original_stock_tx.status, "posted")
        self.assertEqual(original_stock_tx.reference, invoice.invoice_number)

    def test_cannot_cancel_draft_invoice(self):
        invoice = self.create_invoice(quantity=Decimal("1.00"))

        with self.assertRaises(ValueError):
            PurchaseService.cancel_invoice(invoice)

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "draft")

    def test_cannot_cancel_already_cancelled_invoice(self):
        invoice = self.create_invoice(quantity=Decimal("1.00"))
        PurchaseService.post_invoice(invoice)
        invoice.refresh_from_db()
        PurchaseService.cancel_invoice(invoice)
        invoice.refresh_from_db()

        with self.assertRaises(ValueError):
            PurchaseService.cancel_invoice(invoice)

    def test_cancel_rollback_when_reversal_journal_fails(self):
        invoice = self.create_invoice(quantity=Decimal("2.00"))
        PurchaseService.post_invoice(invoice)
        invoice.refresh_from_db()

        with patch.object(
            PurchaseService,
            "_create_reversal_journal_entry",
            side_effect=DjangoValidationError("boom"),
        ):
            with self.assertRaises(DjangoValidationError):
                PurchaseService.cancel_invoice(invoice)

        invoice.refresh_from_db()
        balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(invoice.status, "posted")
        self.assertEqual(balance.quantity, Decimal("2.00"))
        self.assertFalse(
            StockTransaction.objects.filter(
                company=self.company,
                reference=f"REV-{invoice.invoice_number}",
            ).exists()
        )

    def create_invoice(self, quantity):
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
            quantity=quantity,
            unit_price=Decimal("120.00"),
        )
        return invoice


class PurchaseInvoiceCancelAPITestCase(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(
            company=self.company,
            name="Main Branch",
        )
        seed_standard_chart_of_accounts(self.company)

        self.user = User.objects.create_user(
            email="user@example.com",
            password="password",
            full_name="Test User",
            company=self.company,
            branch=self.branch,
        )
        self.client.force_authenticate(self.user)

        self.category = Category.objects.create(
            company=self.company,
            name="Electronics",
        )
        self.unit = Unit.objects.create(
            name="Piece",
            short_name="PCS",
        )
        self.product = Product.objects.create(
            company=self.company,
            category=self.category,
            unit=self.unit,
            name="Laptop",
            product_type="storable",
            average_cost=Decimal("100.00"),
            sale_price=Decimal("150.00"),
        )
        self.warehouse = Warehouse.objects.create(
            company=self.company,
            branch=self.branch,
            name="Main Warehouse",
        )
        self.supplier = Partner.objects.create(
            company=self.company,
            partner_type="supplier",
            name="Supplier A",
        )

    def test_authenticated_user_can_cancel_posted_invoice(self):
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
            quantity=Decimal("1.00"),
            unit_price=Decimal("120.00"),
        )
        PurchaseService.post_invoice(invoice)
        invoice.refresh_from_db()

        response = self.client.post(
            f"/api/purchases/invoices/{invoice.id}/cancel/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "cancelled")
