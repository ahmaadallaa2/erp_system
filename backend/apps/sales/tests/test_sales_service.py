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
from apps.sales.models.sales_invoice import SalesInvoice
from apps.sales.models.sales_invoice_item import SalesInvoiceItem
from apps.sales.services.sales_service import SalesService
from apps.users.models import User


class SalesServiceTestCase(TestCase):
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
        self.assertIsNotNone(invoice.journal_entry_id)
        self.assertEqual(stock_tx.transaction_type, "OUT")
        self.assertEqual(balance.quantity, Decimal("7.00"))

    def test_post_sales_invoice_creates_accounting_entry(self):
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

        SalesService.post_invoice(invoice)
        invoice.refresh_from_db()

        entry = invoice.journal_entry
        self.assertIsNotNone(entry)
        self.assertEqual(entry.status, "posted")
        self.assertEqual(entry.total_debit, entry.total_credit)
        self.assertEqual(entry.total_debit, Decimal("750.00"))

        receivable_line = entry.items.get(account=self.accounts["1003"])
        revenue_line = entry.items.get(account=self.accounts["4001"])
        cogs_line = entry.items.get(account=self.accounts["5001"])
        inventory_line = entry.items.get(account=self.accounts["1004"])

        self.assertEqual(receivable_line.debit, Decimal("450.00"))
        self.assertEqual(receivable_line.partner, self.customer)
        self.assertEqual(revenue_line.credit, Decimal("450.00"))
        self.assertIsNone(revenue_line.partner)
        self.assertEqual(cogs_line.debit, Decimal("300.00"))
        self.assertIsNone(cogs_line.partner)
        self.assertEqual(inventory_line.credit, Decimal("300.00"))
        self.assertIsNone(inventory_line.partner)

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
        self.assertIsNotNone(invoice.journal_entry_id)
        self.assertFalse(invoice.journal_entry.items.filter(account=self.accounts["5001"]).exists())
        self.assertFalse(invoice.journal_entry.items.filter(account=self.accounts["1004"]).exists())

    def test_duplicate_posting_does_not_create_duplicate_entries(self):
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
            quantity=Decimal("1.00"),
            unit_price=Decimal("150.00"),
        )

        SalesService.post_invoice(invoice)
        invoice.refresh_from_db()
        first_entry_id = invoice.journal_entry_id
        entry_count = JournalEntry.objects.count()

        with self.assertRaises(ValueError):
            SalesService.post_invoice(invoice)

        invoice.refresh_from_db()
        self.assertEqual(invoice.journal_entry_id, first_entry_id)
        self.assertEqual(JournalEntry.objects.count(), entry_count)

    def test_accounting_failure_rolls_back_stock_and_invoice_status(self):
        Account.objects.filter(
            company=self.company,
            code="4001",
            is_deleted=False,
        ).delete()

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
            quantity=Decimal("2.00"),
            unit_price=Decimal("150.00"),
        )

        with self.assertRaises(Account.DoesNotExist):
            SalesService.post_invoice(invoice)

        invoice.refresh_from_db()
        balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(invoice.status, "draft")
        self.assertIsNone(invoice.journal_entry_id)
        self.assertEqual(balance.quantity, Decimal("10.00"))

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

    def test_cancel_posted_invoice_restores_stock_and_creates_reversal_journal(self):
        invoice = self.create_invoice(quantity=Decimal("3.00"))
        original_stock_tx = SalesService.post_invoice(invoice)
        invoice.refresh_from_db()
        original_journal_id = invoice.journal_entry_id

        result = SalesService.cancel_invoice(invoice)

        invoice.refresh_from_db()
        balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(invoice.status, "cancelled")
        self.assertEqual(invoice.journal_entry_id, original_journal_id)
        self.assertEqual(balance.quantity, Decimal("10.00"))

        original_entry = JournalEntry.objects.get(id=original_journal_id)
        self.assertEqual(original_entry.status, "posted")

        reversal_entry = result["journal_entry"]
        self.assertNotEqual(reversal_entry.id, original_journal_id)
        self.assertEqual(reversal_entry.status, "posted")
        self.assertEqual(reversal_entry.reference, f"REV-{invoice.invoice_number}")
        self.assertEqual(reversal_entry.total_debit, reversal_entry.total_credit)

        receivable_line = reversal_entry.items.get(account=self.accounts["1003"])
        revenue_line = reversal_entry.items.get(account=self.accounts["4001"])
        cogs_line = reversal_entry.items.get(account=self.accounts["5001"])
        inventory_line = reversal_entry.items.get(account=self.accounts["1004"])

        self.assertEqual(receivable_line.credit, Decimal("450.00"))
        self.assertEqual(receivable_line.partner, self.customer)
        self.assertEqual(revenue_line.debit, Decimal("450.00"))
        self.assertEqual(cogs_line.credit, Decimal("300.00"))
        self.assertEqual(inventory_line.debit, Decimal("300.00"))

        reversal_stock_tx = result["stock_transaction"]
        self.assertIsNotNone(reversal_stock_tx)
        self.assertEqual(reversal_stock_tx.transaction_type, "IN")
        self.assertEqual(reversal_stock_tx.status, "posted")
        self.assertEqual(reversal_stock_tx.reference, f"REV-{invoice.invoice_number}")
        self.assertEqual(reversal_stock_tx.items.get().quantity, Decimal("3.00"))
        self.assertEqual(original_stock_tx.status, "posted")
        self.assertEqual(original_stock_tx.reference, invoice.invoice_number)

    def test_cannot_cancel_draft_invoice(self):
        invoice = self.create_invoice(quantity=Decimal("1.00"))

        with self.assertRaises(ValueError):
            SalesService.cancel_invoice(invoice)

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "draft")

    def test_cannot_cancel_already_cancelled_invoice(self):
        invoice = self.create_invoice(quantity=Decimal("1.00"))
        SalesService.post_invoice(invoice)
        invoice.refresh_from_db()
        SalesService.cancel_invoice(invoice)
        invoice.refresh_from_db()

        with self.assertRaises(ValueError):
            SalesService.cancel_invoice(invoice)

    def test_cancel_rollback_when_reversal_journal_fails(self):
        invoice = self.create_invoice(quantity=Decimal("2.00"))
        SalesService.post_invoice(invoice)
        invoice.refresh_from_db()

        with patch.object(
            SalesService,
            "_create_reversal_journal_entry",
            side_effect=DjangoValidationError("boom"),
        ):
            with self.assertRaises(DjangoValidationError):
                SalesService.cancel_invoice(invoice)

        invoice.refresh_from_db()
        balance = StockBalance.objects.get(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(invoice.status, "posted")
        self.assertEqual(balance.quantity, Decimal("8.00"))
        self.assertFalse(
            StockTransaction.objects.filter(
                company=self.company,
                reference=f"REV-{invoice.invoice_number}",
            ).exists()
        )

    def create_invoice(self, quantity):
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
            quantity=quantity,
            unit_price=Decimal("150.00"),
        )
        return invoice


class SalesInvoiceCancelAPITestCase(APITestCase):
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
        self.customer = Partner.objects.create(
            company=self.company,
            partner_type="customer",
            name="Customer A",
        )
        StockBalance.objects.create(
            company=self.company,
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal("10.00"),
            reserved_quantity=Decimal("0.00"),
        )

    def test_authenticated_user_can_cancel_posted_invoice(self):
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
            quantity=Decimal("1.00"),
            unit_price=Decimal("150.00"),
        )
        SalesService.post_invoice(invoice)
        invoice.refresh_from_db()

        response = self.client.post(
            f"/api/sales/invoices/{invoice.id}/cancel/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "cancelled")
