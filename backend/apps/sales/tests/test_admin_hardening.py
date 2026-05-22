from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.test import RequestFactory, TestCase

from apps.accounting.models import JournalEntry
from apps.accounting.services.chart_of_accounts_seed import seed_standard_chart_of_accounts
from apps.core.models.company import Branch, Company
from apps.inventory.models import Category, Product, StockBalance, Unit, Warehouse
from apps.partners.models import Partner
from apps.sales.admin import SalesInvoiceAdmin, SalesInvoiceItemInline
from apps.sales.models.sales_invoice import SalesInvoice
from apps.sales.models.sales_invoice_item import SalesInvoiceItem
from apps.sales.services.sales_service import SalesService
from apps.users.models import User


class SalesInvoiceAdminHardeningTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/admin/")
        self.request.user = User.objects.create_superuser(
            email="admin@example.com",
            password="testpass123",
            full_name="Admin User",
        )
        self.model_admin = SalesInvoiceAdmin(SalesInvoice, admin.site)
        self.inline_admin = SalesInvoiceItemInline(SalesInvoice, admin.site)

        self.company = Company.objects.create(name="Test Company")
        self.branch = Branch.objects.create(company=self.company, name="Main Branch")
        seed_standard_chart_of_accounts(self.company)
        self.category = Category.objects.create(company=self.company, name="Electronics")
        self.unit = Unit.objects.create(name="Piece", short_name="PCS")
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

    def create_invoice(self, status="draft"):
        return SalesInvoice.objects.create(
            company=self.company,
            branch=self.branch,
            customer=self.customer,
            warehouse=self.warehouse,
            status=status,
        )

    def test_posted_and_cancelled_invoice_cannot_be_changed_or_deleted(self):
        posted_invoice = self.create_invoice(status="posted")
        cancelled_invoice = self.create_invoice(status="cancelled")

        self.assertFalse(self.model_admin.has_change_permission(self.request, posted_invoice))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, posted_invoice))
        self.assertFalse(self.model_admin.has_change_permission(self.request, cancelled_invoice))
        self.assertFalse(self.model_admin.has_delete_permission(self.request, cancelled_invoice))

    def test_status_is_readonly_and_bulk_delete_is_disabled(self):
        readonly_fields = self.model_admin.get_readonly_fields(self.request)
        actions = self.model_admin.get_actions(self.request)

        self.assertIn("status", readonly_fields)
        self.assertIn("posted_by", readonly_fields)
        self.assertIn("posted_at", readonly_fields)
        self.assertIn("cancelled_by", readonly_fields)
        self.assertIn("cancelled_at", readonly_fields)
        self.assertIn("cancellation_reason", readonly_fields)
        self.assertNotIn("delete_selected", actions)

    def test_posted_and_cancelled_item_inlines_are_locked(self):
        posted_invoice = self.create_invoice(status="posted")
        cancelled_invoice = self.create_invoice(status="cancelled")

        for invoice in (posted_invoice, cancelled_invoice):
            self.assertFalse(self.inline_admin.has_add_permission(self.request, invoice))
            self.assertFalse(self.inline_admin.has_change_permission(self.request, invoice))
            self.assertFalse(self.inline_admin.has_delete_permission(self.request, invoice))

    def test_cancel_action_uses_service_and_creates_reversal(self):
        invoice = self.create_invoice()
        SalesInvoiceItem.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=Decimal("2.00"),
            unit_price=Decimal("150.00"),
        )
        SalesService.post_invoice(invoice)
        invoice.refresh_from_db()
        original_entry_id = invoice.journal_entry_id

        with patch.object(self.model_admin, "message_user"):
            self.model_admin.cancel_invoices(
                self.request,
                SalesInvoice.objects.filter(pk=invoice.pk),
            )

        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "cancelled")
        self.assertEqual(invoice.journal_entry_id, original_entry_id)
        self.assertTrue(JournalEntry.objects.filter(reference=f"REV-{invoice.invoice_number}").exists())
